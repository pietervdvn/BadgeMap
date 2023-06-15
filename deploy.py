def downloadToFile(url, filename):
    if url is None:
        raise "downloadToFile cannot work without an URL, it is NONE"
    print("Attempting to save to " + filename)
    r = requests.get(url)
    text = r.text
    r.close()
    print("Received Text is " + str(len(text))+" characters long")
    print("Writing to " + filename)
    with open(filename, "w") as f:
        f.write(text)
        print("Done")
    
def run():
    print("Starting application "+targetdir+"/main_entry.py ...")
    os.chdir(targetdir)
    f = open("main_entry.py")
    script = f.read()
    f.close()
    exec(script)
    
def l():
    os.chdir(targetdir)
    downloadToFile(host + "DeskClock.py", "main_entry.py")
    gc.collect()
    run()
