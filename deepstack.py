from deepstack_sdk import ServerConfig, Detection

config = ServerConfig("http://localhost:5000")
detection = Detection(config, name="best")
def convertDeepstackToDict(deepstackobj):
    output = {"Deers": []}
    for obj in deepstackobj:
        output['Deers'].append({"Label": obj.label, "Confidence": obj.confidence})
    return output
response = detection.detectObject("T_00014.jpeg",output="image_output.jpg")
print(convertDeepstackToDict(response))




