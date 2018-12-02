from MessageHandler import MessageHandler


class GetFileListMessageHandler(MessageHandler):
    def handleMessage(self, message):
        return [
            {
                "name": "somefile1",
                "size": 12345,
                "path": "/firstDir/secondDir/",
                "lastModified": 56789
            },
            {
                "name": "somefile2",
                "size": 12345,
                "path": "/firstDir/secondDir/",
                "lastModified": 56789
            },
            {
                "name": "somefile3",
                "size": 12345,
                "path": "/",
                "lastModified": 56789
            },
            {
                "name": "somefile1",
                "size": 12345,
                "path": "/firstDir",
                "lastModified": 56789
            }
        ]