import base64
class encoded:
    
    def __init__(self, str):
        self.str = str

    def decode(self, formatting):
        b = base64.b64encode(bytes(self.str, 'utf-8')) # bytes
        return b.decode(formatting) # convert bytes to string
        

def b2a_base64(param):
    return encoded(param)
