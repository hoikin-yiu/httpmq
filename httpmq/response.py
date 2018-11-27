class BaseResponse:
    code = None
    msg = None
    extra = None

    def __init__(self, data=None, message=None, **kwargs):
        self.data = data or {}
        self.message = message if message else self.msg
        self.extra = kwargs

    def to_dict(self):
        result = {
            'code': self.code,
            'message': self.message,
            'data': self.data,
        }
        if self.extra:
            result.update(self.extra)
        return result


class SUCCESS(BaseResponse):
    code = 1
    msg = 'HTTPMQ_SUCCEED'


class Fail(BaseResponse):
    code = 2
    msg = 'HTTPMQ_FAILED'


class ParamError(BaseResponse):
    code = 3
    msg = 'HTTPMQ_PARAM_ERROR'
