import asyncio
import json
import logging
import ssl

import aiohttp
import certifi
from aiohttp import web, TCPConnector, ClientTimeout

from .ChatWebReverse.chat_reverse import ChatAgentPool
from .DeepLX.DeeplX import DeepLXPool
from .base_formatter import hybrid_response
from .config import config

logger = logging.getLogger(__name__)


async def handle(request):
    json_data = await request.json()
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("immersive_translate post data:↓↓↓\n%s",
                     json.dumps(json_data, indent=4))
    content = json_data["messages"][1]["content"]
    logger.debug("immersive_translate json->messages->content:\n%s", content)
    text = await hybrid_response(request, content)
    return web.json_response(text=text)


async def start_background_tasks(app):
    for instance in app['chat_agent_pool'].instances.values():
        await instance.register_websocket()
    app['websocket_background_tasks'] = {
        user["EMAIL"]: asyncio.create_task(app['chat_agent_pool'].instances[user["EMAIL"]].wss_client_background())
        for user in config.ACCOUNTS if user["USE"]}


async def cleanup_background_tasks(app):
    logger.debug('start cleanup in background tasks')
    await app['chat_agent_pool'].close()
    for wss_client in app['websocket_background_tasks'].values():
        wss_client.cancel()
        await wss_client
    for session in app['client_sessions'].values():
        await session.close()
        await asyncio.sleep(0)


async def init_app():
    timeout = ClientTimeout(total=40, connect=15, sock_read=30)
    app = web.Application()
    app['client_sessions'] = {
        user["EMAIL"]: aiohttp.ClientSession(
            connector=TCPConnector(ssl=ssl.create_default_context(cafile=certifi.where())),
            raise_for_status=True,
            timeout=timeout)
        for user in config.ACCOUNTS if user["USE"]
    }
    app['chat_agent_pool']: ChatAgentPool = ChatAgentPool(app)
    app['DeepLX'] = DeepLXPool(app)
    app.add_routes([web.post('/v1/chat/completions', handle)])
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    return app


def run():
    app = init_app()
    try:
        web.run_app(app, host='127.0.0.1', port=5050)
    except KeyboardInterrupt:
        logger.info(f"\nServer will shut down...")
    except Exception as e:
        logger.exception(e)
