from tornado.websocket import WebSocketHandler
from tornado.ioloop import PeriodicCallback
from datetime import datetime


class TestWebSocket(WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        self.message = None
        self.loop = PeriodicCallback(self.callback, 2000)
        self.loop.start()
        print("WebSocket opened")

    def on_message(self, message):
        print('message: ', message)
        self.message = message

    def on_close(self):
        print("WebSocket closed")
        self.loop.stop()

    def callback(self):
        if self.message is not None:
            now = datetime.now()
            now = now.strftime('%Y-%m-%d %H:%M:%S')
            self.write_message(now + ': ' + self.message)
