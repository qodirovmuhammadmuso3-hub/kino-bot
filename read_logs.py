with open("bot_error.log", "rb") as f:
    content = f.read()
    try:
        print(content.decode("utf-16le"))
    except:
        print(content.decode("utf-8", errors="ignore"))
