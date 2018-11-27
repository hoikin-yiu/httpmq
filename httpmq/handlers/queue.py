"""implement interface about httpmq"""
import json

import tornado

import response
from exceptions import EmptyQueueException, FullQueueException
from .base import APIHandler

settings = tornado.settings


class QueueHandler(APIHandler):
    async def get(self, **kwargs):
        queue_name = self.get_argument("name")
        if not queue_name:
            return self.response(response.ParamError())

        try:
            pos = await self.get_pos(name=queue_name)
        except EmptyQueueException:
            return self.response(response.Fail(message="HTTPMQ_EMPTY"))
        key = f"{queue_name}:{pos}"
        data = await self.cache.get(key)
        data = json.loads(data) if data else None
        return self.response(response.SUCCESS(data=data))

    async def put(self, **kwargs):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return self.response(response.ParamError())
        queue_name = body.get("name")
        data = body.get("data")
        if not queue_name or data is None:
            return self.response(response.ParamError())

        try:
            pos = await self.put_pos(name=queue_name)
        except FullQueueException:
            return self.response(response.Fail(message="HTTPMQ_FULL"))
        key = f"{queue_name}:{pos}"
        await self.cache.set(key, json.dumps(data))
        return self.response(response.SUCCESS(message="HTTPMQ_PUT_OK"))


class ResetHandler(APIHandler):
    async def get(self, **kwargs):
        queue_name = self.get_argument("name")
        if not queue_name:
            return self.response(response.ParamError())

        queue_keys = await self.cache.keys(f"{queue_name}:*")
        for key in queue_keys:
            await self.cache.delete(key.decode())
        await self.cache.save()
        return self.response(response.SUCCESS(message="HTTPMQ_RESET_OK"))


class ViewHandler(APIHandler):
    async def get(self, **kwargs):
        queue_name = self.get_argument("name")
        position = self.get_argument("position")
        if not queue_name or position is None:
            return self.response(response.ParamError())
        try:
            position = int(position)
        except ValueError:
            return self.response(response.ParamError())
        if not 0 <= position < settings.DEFAULT_MAX_QUEUE_NUM:
            return self.response(response.ParamError())

        put_pos = await self.read_put_pos(queue_name)
        get_pos = await self.read_get_pos(queue_name)
        if put_pos is not None:
            if get_pos is not None:
                if put_pos > get_pos:
                    if not get_pos <= position < put_pos:
                        return self.response(response.Fail())
                if put_pos == get_pos:
                    return self.response(response.Fail(message="HTTPMQ_EMPTY"))
                if put_pos < get_pos:
                    if put_pos <= position < get_pos:
                        return self.response(response.Fail())
            else:
                if position >= put_pos:
                    return self.response(response.Fail())
        else:
            return self.response(response.Fail())

        key = f"{queue_name}:{position}"
        data = await self.cache.get(key)
        data = json.loads(data) if data else None
        return self.response(response.SUCCESS(data=data))


class StatusHandler(APIHandler):
    async def get(self, **kwargs):
        queue_name = self.get_argument("name")
        if not queue_name:
            return self.response(response.ParamError())

        put_pos = await self.read_put_pos(queue_name)
        get_pos = await self.read_get_pos(queue_name)
        if put_pos is not None:
            if get_pos is not None:
                unread = abs(put_pos - get_pos)
            else:
                unread = put_pos
        else:
            unread = None
        return self.response(response.SUCCESS(data={
            "name": queue_name,
            "put_pos": put_pos,
            "get_pos": get_pos,
            "unread": unread,
        }))
