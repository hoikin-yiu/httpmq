"""implement interface about httpmq"""
import json

import tornado

import response
from exceptions import (
    EmptyQueueException, FullQueueException, InvalidPositionException,
    QueueNotExistsException
)
from queues import RedisQueue as Queue
from .base import APIHandler

settings = tornado.settings


class QueueHandler(APIHandler):
    async def get(self, **kwargs):
        name = self.get_argument("name")
        if not name:
            return self.response(response.ParamError())

        queue = Queue(name)
        try:
            data = await queue.get()
        except EmptyQueueException:
            return self.response(response.Fail(message="HTTPMQ_EMPTY"))
        except QueueNotExistsException:
            return self.response(response.Fail(message="HTTPMQ_NOT_EXISTS"))
        return self.response(response.SUCCESS(data=data))

    async def put(self, **kwargs):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return self.response(response.ParamError())
        name = body.get("name")
        data = body.get("data")
        if not name or data is None:
            return self.response(response.ParamError())

        queue = Queue(name)
        try:
            await queue.put(data)
        except FullQueueException:
            return self.response(response.Fail(message="HTTPMQ_FULL"))
        return self.response(response.SUCCESS(message="HTTPMQ_PUT_OK"))


class ResetHandler(APIHandler):
    async def get(self, **kwargs):
        name = self.get_argument("name")
        if not name:
            return self.response(response.ParamError())

        queue = Queue(name)
        try:
            await queue.reset()
        except QueueNotExistsException:
            return self.response(response.Fail(message="HTTPMQ_NOT_EXISTS"))
        return self.response(response.SUCCESS(message="HTTPMQ_RESET_OK"))


class ViewHandler(APIHandler):
    async def get(self, **kwargs):
        name = self.get_argument("name")
        position = self.get_argument("position")
        if not name or position is None:
            return self.response(response.ParamError())
        try:
            position = int(position)
        except ValueError:
            return self.response(response.ParamError())
        if not 0 <= position < settings.DEFAULT_MAX_QUEUE_NUM:
            return self.response(response.ParamError())

        queue = Queue(name)
        try:
            data = await queue.view(position)
        except InvalidPositionException:
            return self.response(response.Fail())
        except EmptyQueueException:
            return self.response(response.Fail(message="HTTPMQ_EMPTY"))
        except QueueNotExistsException:
            return self.response(response.Fail(message="HTTPMQ_NOT_EXISTS"))
        return self.response(response.SUCCESS(data=data))


class StatusHandler(APIHandler):
    async def get(self, **kwargs):
        name = self.get_argument("name")
        if not name:
            return self.response(response.ParamError())

        queue = Queue(name)
        try:
            data = await queue.status()
        except QueueNotExistsException:
            return self.response(response.Fail(message="HTTPMQ_NOT_EXISTS"))
        return self.response(response.SUCCESS(data=data))
