"""master-worker model"""
import asyncio
import os
import signal
import threading
import time

import redis
import tornado
import tornado.ioloop
import tornado.web
import uvloop

settings = tornado.settings


class Worker:
    pool = redis.ConnectionPool(host=settings.REDIS_HOST,
                                port=settings.REDIS_PORT,
                                socket_keepalive=True)
    cache = redis.StrictRedis(connection_pool=pool)
    exit_signal = [
        signal.SIGINT, signal.SIGQUIT, signal.SIGTERM,
        signal.SIGHUP
    ]

    def __init__(self, port=8200, daemon=True, app=None):
        self.port = port
        self.daemon = daemon
        self.app = app

    @staticmethod
    def master_signal_handler(signum, frame):
        """handle signal of child process"""
        Worker.cache.save()
        os._exit(os.EX_OK)

    @staticmethod
    def worker_signal_handler(signum, frame):
        """handle signal of worker process"""
        os.kill(0, signal.SIGTERM)
        os._exit(os.EX_OK)

    @staticmethod
    def sync_handler():
        """sync data from memory to disk"""
        while True:
            time.sleep(settings.INTERVAL)
            Worker.cache.save()

    def run(self):
        if self.daemon:
            pid = os.fork()
            if pid < 0:
                os._exit(os.EX_SOFTWARE)
            # main process quit
            if pid > 0:
                os._exit(os.EX_OK)
        # start child process:
        os.umask(0)
        try:
            os.setsid()
        except OSError:
            pass
        # secondly forking
        pid2 = os.fork()
        if pid2 < 0:
            os._exit(os.EX_SOFTWARE)
        # master:
        if pid2 > 0:
            self.start_master()

        # Start : start httpmq worker process
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)
        for s in self.exit_signal:
            signal.signal(s, self.worker_signal_handler)
        # create sync thread
        sync_thread = threading.Thread(target=self.sync_handler, args=())
        sync_thread.start()

        # start handle http request:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        self.app.listen(self.port)
        tornado.ioloop.IOLoop.current().start()

    def start_master(self):
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)
        for s in self.exit_signal:
            signal.signal(s, self.master_signal_handler)
        while True:
            worker_pid, status = os.wait()
            if status < 0:
                continue
            time.sleep(10)
            pid2 = os.fork()
            if pid2 == 0:
                # if worker process was terminated,
                # break loop and jump to Start:
                break
