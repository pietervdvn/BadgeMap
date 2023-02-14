class Response:

    def __init__(self, text):
        self.text = text

    def close(self):
        pass


def request(param, url, param1, param2, headers=None):
    return Response(
        'BEGIN:VEVENT\nLOCATION:here\nDTSTART:20220705\nDTEND:20220706\nSUMMARY:some random event\nEND:VEVENT\n')
