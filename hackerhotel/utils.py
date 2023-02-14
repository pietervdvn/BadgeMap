import urequests as requests


def downloadToFile(url, filename):
    if url is None:
        raise "downloadToFile cannot work without an URL, it is NONE"
    r = requests.get(url)
    print("Attempting to save to " + filename)
    text = r.text
    r.close()
    print("Received Text is " + str(len(text))+" characters long")
    print("Writing to " + filename)
    with open(filename, "w") as f:
        f.write(text)
        print("Done")