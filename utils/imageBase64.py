import base64

def saveImageFromBase64(imgstring, filename):
    imgdata = base64.b64decode(imgstring)
    with open(filename, 'wb') as f:
        f.write(imgdata)