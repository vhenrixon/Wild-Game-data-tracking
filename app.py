

from pymongo import MongoClient
import pymongo
import os
import getpass, imaplib
import os
import sys
import email
import base64
from tqdm import tqdm
from PIL import Image
from PIL.ExifTags import TAGS
import schedule
from datetime import datetime
import time
from email import utils
from deepstack_sdk import ServerConfig, Detection
import urllib
import random

server_key = ""

email_name = ""
email_key = ""

try:
    # try to instantiate a client instance
    client = MongoClient(
        server_key
    )

    # print the version of MongoDB server if connection successful
    print ("server version:", client.server_info()["version"])

    # get the database_names from the MongoClient()
    database_names = client.list_database_names()

    dataDB = client.data
    deerData = dataDB.deerData
    sinceDb = dataDB.since

except pymongo.errors.ServerSelectionTimeoutError as err:
    # set the client and DB name list to 'None' and `[]` if exception
    client = None
    database_names = []

    # catch pymongo.errors.ServerSelectionTimeoutError
    print ("pymongo ERROR:", err)



last_possible_img_date = None
HOME = [-84.5315,32.95369]   
BARN_FEED = [-84.54343, 32.95487,] 
TAVERN_CREEK_FEED = [-84.54374, 32.96118,]
CANE_CREEK_FEED = [-84.54068, 32.96019,]
TURKEY_FEED = [-84.53908,32.95532]
RIVER_RD_FIELD = [-84.53769,32.9596]
DUCK_FIELD = [-84.53755,32.96221]
HIDEAWAY_FEED = [-84.53463,32.95602]
WATER_TOWER_FIELD = [-84.5398,32.95104]
RIDGE_RD_FEED = [-84.53174,32.95108]
RIDGE_FIELD = [-84.53147,32.95368]
HONEYHOLE = [-84.5263, 32.9511]
RIDGE_FEED = [-84.527103,32.955043]
FLINT_RIVER_FEILD = [-84.52072,32.95185]
TAVERN_CREEK_CROSSIN = [-84.54261,32.96223]
PUMP = [32.95884,84.54275]
#Deepstack connection 
config = ServerConfig('http://deep:5000')
detection = Detection(config, name="best")

def detectDeer(imgBinary, save_image=False):
    if save_image:
        file_name = random.randint(0, 1000000)
        response = detection.detectObject(imgBinary, output="image-"+file_name+".jpg")
    else:
        response = detection.detectObject(imgBinary)
    return response

def convertDateTimeString(string): 
    # 2021:07:20 02:38:40 -> #DD-Month-YYYY
    return (datetime.strptime(string, "%Y:%m:%d %I:%M:%S")).strftime('%d-%b-%Y')

def convertDeepstackToDict(deepstackobj):
    output = {"Deers": []}
    for obj in deepstackobj:
        output['Deers'].append({"Label": obj.label, "Confidence": obj.confidence})
    return output

def downloadPicture(mail_ids, imap_ssl): 

    for mail_id in tqdm(mail_ids, desc="Downlowing pictures...",ascii=False, ncols=75):
                resp_code, mail_data = imap_ssl.fetch(mail_id, '(RFC822)') ## Fetch mail data.
                message = email.message_from_bytes(mail_data[0][1])
                if message.get_content_maintype() != 'multipart':
                    return
                for part in tqdm(message.walk(), desc="Downloading Specific deer pictures...",ascii=False, ncols=75):
                    if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                        if (part.get_filename()[-4:] == "HTML"):
                            continue
                        else:
                            open("attachments" + '/' + part.get_filename(), 'wb').write(part.get_payload(decode=True))
                            new_file_name = "attachments" + '/' + str(mail_id)+part.get_filename()
                            os.rename("attachments" + '/' + part.get_filename(),new_file_name)
                            try:
                                meta_data = getMetaData(new_file_name, str(mail_id)+part.get_filename())
                                last_possible_img = meta_data["DateTime"] # In case of crash
                                
                                with open("attachments" + '/' + str(mail_id)+part.get_filename(), "rb") as f:
                                    img_content = f.read()
                                    deer_data = convertDeepstackToDict(detectDeer(img_content, save_image=False))
                                    if (findLocation(meta_data["Location"]) != "ERROR"):
                                        deer_data.update({"locationName": meta_data["Location"],"location": findLocation(meta_data["Location"]), "datetime": meta_data["DateTime"]})
                                        deerData.insert_one(deer_data)
                                    os.remove(new_file_name)
                            except TypeError:
                                continue

def getSearchMailID(since, imap_ssl, inverse=False, reconnecting=False): 
    if inverse and not reconnecting:
        resp_code, mails = imap_ssl.search(None,'FROM', '"CuddeLink"', 'SENTBEFORE', since)
    elif not inverse and not reconnecting:
        resp_code, mails = imap_ssl.search(None, 'FROM', '"CuddeLink"', 'SENTSINCE', since)
    elif reconnecting and inverse: 
        resp_code, mails = imap_ssl.search(None,'FROM', '"CuddeLink"', 'SENTBEFORE', since)
    elif reconnecting and not inverse:
        resp_code, mails = imap_ssl.search(None, 'FROM', '"CuddeLink"', 'SENTSINCE', since)

    mail_ids = mails[0].decode().split()

    return mail_ids

def getMailSince(since, inverse=False):

    print("Getting mail")
    detach_dir = '.'
    if 'attachments' not in os.listdir(detach_dir):
        os.mkdir('attachments')

    while True: 
        imap_ssl = imaplib.IMAP4_SSL(host="imap.gmail.com", port=imaplib.IMAP4_SSL_PORT)
        print("Connection Object : {}".format(imap_ssl))

        print("Logging into mailbox...")
        resp_code, response = imap_ssl.login(email_name, email_key)
        try:
            resp_code, mail_count = imap_ssl.select(mailbox="INBOX", readonly=True)
            mail_ids = getSearchMailID(since,imap_ssl, inverse)
            downloadPicture(mail_ids, imap_ssl)
            break
        except imaplib.IMAP4_SSL.abort: 
            resp_code, mail_count = imap_ssl.select(mailbox="INBOX", readonly=True)
            mail_ids = getSearchMailID(convertDateTimeString(last_possible_img_date), imap_ssl, inverse, reconnecting=True)
            downloadPicture(mail_ids, imap_ssl)
            break
        print("\nClosing selected mailbox....")
        imap_ssl.close()
        
def getMetaData(image, name):
    image_data = {"iamge_name": name}
    for tag, value in Image.open(image)._getexif().items():
        if TAGS.get(tag) == "UserComment":

            temp = [i for i in value.split(',')]
            image_data.update({str(TAGS.get(tag)): str(temp)})
            location = temp[16]
            image_data.update({"Location": location[3:len(temp[16])]})
        else:
            image_data.update({str(TAGS.get(tag)): str(value)})
    return image_data

def sinceCheck():
    # A simple check to see if the mongodb has a last since the photos have been retrieved 
    lastDate = sinceDb.count_documents({"name": "since"})
    print(lastDate)
    if lastDate > 0:
        return False
    else:
        return True

def getDay():
    #DD-Month-YYYY
    return datetime.now().strftime('%d-%b-%Y')

def findLocation(location):
    if location == "HOME":
        return HOME
    elif location == "BARN FEED":
        return BARN_FEED
    elif location == "TAVERN CREEK FEED":
        return TAVERN_CREEK_FEED
    elif location == "CANE CREEK FEED":
        return CANE_CREEK_FEED
    elif location == "TURKEY FEED":
        return TURKEY_FEED
    elif location == "RIVER RD FIELD":
        return RIVER_RD_FIELD
    elif location == "DUCK FIELD":
        return DUCK_FIELD
    elif location == "HIDEAWAY FEED":
        return HIDEAWAY_FEED
    elif location == "WATER TOWER FIELD":
        return WATER_TOWER_FIELD
    elif location == "RIDGE RD FEED":
        return RIDGE_RD_FEED
    elif location == "RIDGE FIELD":
        return RIDGE_FIELD
    elif location == "HONEYHOLE":
        return HONEYHOLE
    elif location == "RIDGE FEED":
        return RIDGE_FEED
    elif location == "FLINT RIVER FEILD":
        return FLINT_RIVER_FEILD
    elif location == "TAVERN CREEK CROSSIN":
        return TAVERN_CREEK_CROSSIN
    elif location == "PUMP":
        return PUMP
    else:
        return "ERROR"

def runtime():
    current_time = getDay()
    if sinceCheck():
        sinceDb.insert_one({
            "name": "since",
            "date": current_time
        })
        

        getMailSince(current_time, True)

    else:
        date = sinceDb.find_one({"name":"since"})

        getMailSince(date['date'])
        sinceDb.update_one({'name':"since"}, {"$set":{
            "date": current_time
        }})


if __name__ == "__main__":

    schedule.every().day.at("00:00").do(runtime)
    print("Schedule Task")
    while True:
        
        # Checks whether a scheduled task 
        # is pending to run or not
        schedule.run_pending()
        print(str(schedule.next_run()))
        time.sleep(1)