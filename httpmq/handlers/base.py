import tornado.web


class BaseHandler(tornado.web.RequestHandler):

    def response(self, response, status=200, headers=None):
        if headers and isinstance(headers, dict):
            for key, value in headers.items():
                self.set_header(key, value)

        self.set_status(status_code=status)
        self.finish(response.to_dict())


class APIHandler(BaseHandler):
    pass
