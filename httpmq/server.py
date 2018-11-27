#!/usr/bin/env python
import os
import sys
from importlib import import_module

import click
import tornado.web


def make_app(profile="develop"):
    settings = import_module(f"httpmq.settings.{profile}")
    tornado.settings = settings

    from httpmq.url import urls
    assert isinstance(urls, (list, tuple)), 'urls must be list or tuple'
    app = tornado.web.Application(urls, debug=settings.DEBUG)
    return app


@click.command()
@click.option("--port", default=8200)
@click.option("--profile", default="develop")
@click.option("--daemon", default=False)
def serve(port, profile, daemon):
    app = make_app(profile=profile)

    from worker import Worker
    worker = Worker(port=port, daemon=daemon, app=app)
    worker.run()


if __name__ == '__main__':
    current_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, current_path)
    serve()
