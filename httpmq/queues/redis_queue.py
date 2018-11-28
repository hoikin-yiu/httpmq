import json

import aredis
import tornado

from exceptions import (
    EmptyQueueException, FullQueueException, InvalidPositionException
)
from .base import Queue

settings = tornado.settings
cache = aredis.StrictRedis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT
)
__all__ = ["RedisQueue"]


class RedisQueue(Queue):
    _cache = cache

    def __init__(self, name):
        self.name = name

    async def get(self):
        try:
            pos = await self._get_pos()
        except EmptyQueueException:
            raise
        key = f"{self.name}:{pos}"
        data = await self._cache.get(key)
        data = json.loads(data) if data else None
        return data

    async def put(self, data):
        try:
            pos = await self._put_pos()
        except FullQueueException:
            raise
        key = f"{self.name}:{pos}"
        await self._cache.set(key, json.dumps(data))

    async def status(self):
        put_pos = await self._read_put_pos()
        get_pos = await self._read_get_pos()
        if put_pos is not None:
            if get_pos is not None:
                unread = abs(put_pos - get_pos)
            else:
                unread = put_pos
        else:
            unread = None
        return {
            "name": self.name,
            "put_pos": put_pos,
            "get_pos": get_pos,
            "unread": unread,
        }

    async def view(self, position):
        put_pos = await self._read_put_pos()
        get_pos = await self._read_get_pos()
        if put_pos is not None:
            if get_pos is not None:
                if put_pos > get_pos:
                    if not get_pos <= position < put_pos:
                        raise InvalidPositionException()
                if put_pos == get_pos:
                    raise EmptyQueueException()
                if put_pos < get_pos:
                    if put_pos <= position < get_pos:
                        raise InvalidPositionException()
            else:
                if position >= put_pos:
                    raise InvalidPositionException()
        else:
            raise InvalidPositionException()

        key = f"{self.name}:{position}"
        data = await self._cache.get(key)
        data = json.loads(data) if data else None
        return data

    async def reset(self):
        keys = await self._cache.keys(f"{self.name}:*")
        for key in keys:
            await self._cache.delete(key.decode())
        await self._cache.save()

    async def _get_pos(self):
        """get current position to read, head"""
        put_pos_key = f"{self.name}:put_pos"
        get_pos_key = f"{self.name}:get_pos"
        async with await self._cache.pipeline() as pipe:
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

    async def _put_pos(self):
        """get current position to put in, tail"""
        put_pos_key = f"{self.name}:put_pos"
        get_pos_key = f"{self.name}:get_pos"
        async with await self._cache.pipeline() as pipe:
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

    async def _read_put_pos(self):
        key = f"{self.name}:put_pos"
        put_pos = await self._cache.get(key)
        return int(put_pos.decode()) if put_pos else None

    async def _read_get_pos(self):
        key = f"{self.name}:get_pos"
        get_pos = await self._cache.get(key)
        return int(get_pos.decode()) if get_pos else None
