import aredis
import tornado.web

from exceptions import EmptyQueueException, FullQueueException

settings = tornado.settings
cache = aredis.StrictRedis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT
    )


class BaseHandler(tornado.web.RequestHandler):

    def response(self, response, status=200, headers=None):
        if headers and isinstance(headers, dict):
            for key, value in headers.items():
                self.set_header(key, value)

        self.set_status(status_code=status)
        self.finish(response.to_dict())


class APIHandler(BaseHandler):
    cache = cache

    async def get_pos(self, name):
        """get current position to read, head"""
        put_pos_key = f"{name}:put_pos"
        get_pos_key = f"{name}:get_pos"
        async with await self.cache.pipeline() as pipe:
            while True:
                try:
                    await pipe.watch(get_pos_key)
                    current_get_pos = await pipe.get(get_pos_key)
                    current_get_pos = int(current_get_pos.decode()) \
                        if current_get_pos else None
                    current_put_pos = await pipe.get(put_pos_key)
                    current_put_pos = int(current_put_pos.decode()) \
                        if current_put_pos else None
                    if current_get_pos is None:
                        if current_put_pos is None:
                            raise EmptyQueueException()
                        else:
                            current_get_pos = 0
                    elif current_get_pos == current_put_pos:
                        # current_put_pos is always empty
                        raise EmptyQueueException()
                    if current_get_pos == settings.DEFAULT_MAX_QUEUE_NUM:
                        next_get_pos = 0
                    else:
                        next_get_pos = current_get_pos + 1
                    pipe.multi()
                    await pipe.set(get_pos_key, next_get_pos)
                    await pipe.execute()
                    break
                except aredis.WatchError:
                    continue
                except EmptyQueueException:
                    raise
        return current_get_pos

    async def put_pos(self, name):
        """get current position to put in, tail"""
        put_pos_key = f"{name}:put_pos"
        get_pos_key = f"{name}:get_pos"
        async with await self.cache.pipeline() as pipe:
            while True:
                try:
                    await pipe.watch(put_pos_key)
                    current_put_pos = await pipe.get(put_pos_key)
                    current_put_pos = int(current_put_pos.decode()) \
                        if current_put_pos else None
                    current_get_pos = await pipe.get(get_pos_key)
                    current_get_pos = int(current_get_pos.decode())\
                        if current_get_pos else None
                    if current_put_pos is None:
                        # init
                        current_put_pos = 0
                    elif current_put_pos == settings.DEFAULT_MAX_QUEUE_NUM:
                        if not current_get_pos:
                            raise FullQueueException()
                        else:
                            current_put_pos = 0
                    elif current_put_pos + 1 == current_get_pos:
                        # current_get_pos is unread
                        raise FullQueueException()
                    next_put_pos = current_put_pos + 1
                    pipe.multi()
                    await pipe.set(put_pos_key, next_put_pos)
                    await pipe.execute()
                    break
                except aredis.WatchError:
                    continue
                except FullQueueException:
                    raise
        return current_put_pos

    async def read_put_pos(self, name):
        key = f"{name}:put_pos"
        put_pos = await self.cache.get(key)
        return int(put_pos.decode()) if put_pos else None

    async def read_get_pos(self, name):
        key = f"{name}:get_pos"
        get_pos = await self.cache.get(key)
        return int(get_pos.decode()) if get_pos else None
