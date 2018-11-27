from handlers.queue import (
    QueueHandler, StatusHandler, ResetHandler, ViewHandler
)

urls = [
    (r"/queue/", QueueHandler),
    (r"/status/", StatusHandler),
    (r"/reset/", ResetHandler),
    (r"/view/", ViewHandler),
]
