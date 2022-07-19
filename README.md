# Deer-Tracker

## Purpose / Workings
The purpose of this app is to collect data on the deer population through game cameras. The game camera is the cuddle link camera that sends the game images through email. Additionally, the program uses a deep stack image recognition library to identify bucks, does, and turkeys in the photos and then sends the animal data to MongoDB. The data is then organized using mongocharts. NOTE, this program has been made with some hardcoded parts related to my farm. Hopefully, the program can be modular in the future for more public use. 

### Before
 ![Before](https://github.com/vhenrixon/Wild-Game-data-tracking/blob/main/img/2_original.jpeg)
### After
![After](https://github.com/vhenrixon/Wild-Game-data-tracking/blob/main/img/2_image_output.jpg)
### Data Chart (Mongo Charts)
![Mongo Chart](https://github.com/vhenrixon/Wild-Game-data-tracking/blob/main/img/Screen%20Shot%202022-07-19%20at%2011.21.15%20AM.png)
## Setup

Found in the app.py, there are three variables server_key, which is for the MongoDB key, the email_key(password), and email_name(address). NOTE, this app only works/tested with Gmail servers. 

After finishing the configuration run the command: docker-compose up

## Making your own dataset

The medium article below demonstrate quite well how to create a custom model and when done place the best.pt in /custom_model

https://medium.com/deepquestai/detect-any-custom-object-with-deepstack-dd0a824a761e