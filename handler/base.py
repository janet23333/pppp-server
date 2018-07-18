import json

import jwt
import tornado.auth
import tornado.escape
import tornado.gen
import tornado.httpclient
import tornado.httputil
import tornado.ioloop
import tornado.locale
import tornado.options
import tornado.web
from jwt import InvalidTokenError
from tornado.ioloop import PeriodicCallback
from tornado.log import app_log
from tornado.web import HTTPError
from tornado.websocket import WebSocketHandler

from common import util
from conf import settings

json_encoder = util.json_encoder
json_decoder = util.json_decoder


class BaseHandler(tornado.web.RequestHandler):
    """
        BaseHandler
        override class method to adapt special demands
    """

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, PUT, GET, DELETE, OPTIONS')
        self.set_header('Access-Control-Allow-Headers', 'x-requested-with,content-type,token')

    def options(self, *argus):
        # no body
        self.set_status(204)
        self.finish()

    def _get_argument(self, name, default, source, strip=True):
        args = self._get_arguments(name, source, strip=strip)
        if not args:
            if default is self._ARG_DEFAULT:
                raise tornado.web.MissingArgumentError(name)
            return default
        return args[0]

    def write_error(self, status_code, **kwargs):
        self.render_json_response(code=status_code, msg=self._reason)

    def log_exception(self, typ, value, tb):
        if isinstance(value, HTTPError):
            if value.log_message:
                warning_format = '%d %s: ' + value.log_message
                args = ([value.status_code, self._request_summary()] + list(value.args))
                app_log.warning(warning_format, *args)

        app_log.error('Exception: %s\n%r', self._request_summary(), self.request, exc_info=(typ, value, tb))

    def get_user(self):
        token = self.get_query_argument('token', None)  # from url
        if not token:
            headers = self.request.headers  # from headers
            token = headers["Token"] if "Token" in headers.keys() else None
        if not token:
            return None
        try:
            payload = jwt.decode(token, settings['token_secret'], algorithms=['HS256'])
            return payload
        except InvalidTokenError as e:
            return None

    def render_json_response(self, **kwargs):
        """
            Encode dict and return response to client
        """
        _callback = self.get_query_argument('callback', None)
        if _callback:
            # return jsonp
            self.set_status(200, kwargs.get('msg', None))
            self.finish('{}({})'.format(_callback, json_encoder(kwargs)))
        else:
            self.set_status(kwargs['code'], kwargs.get('msg', None))
            self.set_header('Content-Type', 'application/json;charset=utf-8')
            _format = self.get_query_argument('_format', None)
            if _format:
                # return with indent
                self.finish(json.dumps(json.loads(json_encoder(kwargs)), indent=4))
            else:
                self.finish(json_encoder(kwargs))

    def prepare(self):
        """
            prepare session and post arguments
        """
        self.user = self.get_user()
        self.body_arguments = {}
        self.url_arguments = {}

        # 把body里面的参数，放在body_arguments里面
        if self.request.body:
            try:
                self.body_arguments = json_decoder(tornado.escape.native_str(self.request.body))

                from handler.token import TokenHandler
                if not isinstance(self, TokenHandler):
                    app_log.info(self.body_arguments)
            except json.decoder.JSONDecodeError:
                """invalid  json arguments"""
                raise HTTPError(status_code=400, reason="JSONDecodeError,invalid json arguments")

        # 把url里面的参数，放在url_arguments(已经把无关属性剔除)
        if self.request.query_arguments:
            q_arguments = {}
            for key in self.request.query_arguments.keys():
                value = self.request.query_arguments[key][0].decode()
                q_arguments.update({key: value})

            # pop 无关字段
            q_arguments.pop("_format", None)
            q_arguments.pop("callback", None)
            q_arguments.pop("token", None)

            # q_arguments.pop("page", None)
            # q_arguments.pop("page_size", None)

            self.url_arguments = q_arguments

    def on_finish(self):
        self.body_arguments = {}
        self.url_arguments = {}


class BaseWebSocket(WebSocketHandler):
    def initialize(self):
        self.settings['websocket_ping_interval'] = 5
        self.message = None

    def render_json_response(self, res, code=200, msg='', binary=False):
        if code != 200:
            app_log.error(msg)

        response = {"code": code, "msg": msg, "res": res}
        response = json_encoder(response)
        return self.write_message(response, binary=binary)

    def check_origin(self, origin):
        return True

    def open(self, callback_timeout=500):
        app_log.info('WebSocket open')
        self.loop = PeriodicCallback(self.callback, callback_timeout)
        self.loop.start()

    def on_close(self):
        app_log.info("WebSocket closed")
        self.loop.stop()

    def callback(self):
        raise NotImplementedError

    def on_message(self, message):
        app_log.info(message)
