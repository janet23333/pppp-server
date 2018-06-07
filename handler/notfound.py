from handler.base import BaseHandler


class NotFoundHandler(BaseHandler):
    def get(self):
        return self.render_json_response(code=404, msg="not found")

    def post(self):
        return self.render_json_response(code=404, msg="not found")
