import os
import asyncio
import logging

from aiohttp import web

from ddtrace import tracer
from ddtrace.contrib.aiohttp import trace_app

FORMAT = ('%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] '
          '[dd.trace_id=%(dd.trace_id)s dd.span_id=%(dd.span_id)s] '
          '- %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger(__name__)
log.level = logging.INFO

# env vars for deploying purpose
DATADOG_TRACER = os.getenv('DATADOG_TRACER', 'localhost')
HOSTNAME = os.getenv('APP_HOSTNAME', '127.0.0.1')
PORT = int(os.getenv('APP_PORT', '8000'))
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'statics')

# configure the tracer
tracer.configure(hostname=DATADOG_TRACER)


async def handle(request):
    # basic handling
    name = request.match_info.get("name", "Anonymous")
    text = "Hello {}".format(name)
    log.debug(text)
    # trigger some async work
    await some_work(request)

    # close the request
    return web.Response(text=text)


async def some_work(request):
    # simulating a slow operation that would yield something;
    # this action is traced
    with tracer.trace('async.work'):
        log.info('sleeping')
        await asyncio.sleep(2)


# your application
app = web.Application()
app.router.add_get("/users", handle)
app.router.add_get("/users/{name}", handle)
app.router.add_static('/statics', STATIC_DIR)

# asynchronous tracing
trace_app(app, tracer, service='async-web')
web.run_app(app, host=HOSTNAME, port=PORT)
