import asyncio
import base64
import json
import re
import uuid
from asyncio import QueueFull
from collections import namedtuple
from dataclasses import dataclass

import aiohttp

from TranslateGuard.base_exceptions import UnequalParagraphCountException, ErrorMsg
from TranslateGuard.base_formatter import build_result
from TranslateGuard.base_message_enum import DebugInfoMsg, Service
from TranslateGuard.config import config
from TranslateGuard.utils import SingletonMeta
from . import logger
from .auth_handler import get_cookies, save_cookies, get_access_token
from .exceptions import ChatWebReverseException, ChatWebReverseErrorType
from .formatter import build_prompt_web_chat_gpt
from .headers import get_headers_for_del_conversation, get_headers_for_general, get_headers_for_conversation, \
    get_wss_headers
from .playload import get_req_con_playload
from .uc_back import SeleniumRequests

User = namedtuple('User', ['EMAIL', 'PASSWORD', 'USE'])


@dataclass
class Conversation:
    user: User
    is_echo: bool = False
    is_new: bool = True
    conversation_id: str | None = None
    current_node: str = str(uuid.uuid4())


PATTERN_DATA = re.compile(r'data: (.*)', re.DOTALL)


class ChatgptAgent:
    def __init__(self, user: User, session: aiohttp.ClientSession):
        self.user = user
        self.sl = None  # Selenium instance
        self.lock = asyncio.Lock()
        self.cookies = self._init_cookies()
        self.access_token = self._get_access_token()
        self.session = self._update_cookies_for_session(session)
        self.conversation = Conversation(user=user)
        self.wss_url = None
        self.wss_client = None
        self.websocket_request_id = str(uuid.uuid4())
        self.queue = asyncio.Queue(maxsize=1)
        self.proxy = "http://127.0.0.1:7890"

    # @retry(e_type_list=[ErrorMsg.ConnectionError])
    async def del_conversation_remote(self, again: bool = False) -> bool | None:
        resp = None
        try:
            resp = await self.session.patch(
                url=f"https://chat.openai.com/backend-api/conversation/{self.conversation.conversation_id}",
                headers=get_headers_for_del_conversation(self.access_token, self.conversation.conversation_id),
                json={"is_visible": False})
            resp_json = await resp.json()
            is_done = resp_json["success"]
            if is_done:
                logger.info(f"SUCCESS: Delete current conversation {self.user.EMAIL}:\n {resp_json}")
            return is_done
        except aiohttp.ClientResponseError as e:
            if 400 <= e.status < 500:
                logger.error(ChatWebReverseErrorType.ERROR_4XX, Service.ChatWebGpt, self.user.EMAIL, resp.status,
                             resp.text)
                if not again:
                    if not self.sl:
                        self.sl = SeleniumRequests(self.user)
                    await self._update_cookies()
                    await self.del_conversation_remote(again=True)
                else:
                    logger.error(ChatWebReverseErrorType.RETRY_FAILED, Service.ChatWebGpt, self.user.EMAIL, resp.status)
            else:
                logger.error(ChatWebReverseErrorType.ERROR_5XX, Service.ChatWebGpt, self.user.EMAIL, resp.status,
                             resp.text)
                if not again:
                    await self.del_conversation_remote(again=True)
                else:
                    logger.error(ChatWebReverseErrorType.RETRY_FAILED, Service.ChatWebGpt, self.user.EMAIL, resp.status)
        except Exception as e:
            logger.exception(e)

    async def close(self):
        if self.conversation.is_echo:
            self.cookies = [{'name': c.key, 'value': c.value, 'domain': c['domain'], 'path': c['path']}
                            for c in self.session.cookie_jar]
            save_cookies(self.user.EMAIL, self.cookies)
            if config.SHOULD_DEL_CON:
                async with self.lock:
                    await self.del_conversation_remote()

    def _init_cookies(self):
        try:
            return get_cookies(self.user.EMAIL)
        except ChatWebReverseException as e:
            if e.error_type == ChatWebReverseErrorType.NoCookies:
                logger.warning(e)

    def _get_access_token(self) -> str | None:
        try:
            return get_access_token(self.user.EMAIL)
        except ChatWebReverseException as e:
            if e.error_type == ChatWebReverseErrorType.NoAccessToken:
                logger.warning(e)
        except Exception:
            raise

    def _update_cookies_for_session(self, session: aiohttp.ClientSession) -> aiohttp.ClientSession:
        cookies_ = {cookie['name']: cookie['value']
                    for cookie in self.cookies if cookie['name'] != "__Host-next-auth.csrf-token"}
        session.cookie_jar.update_cookies(cookies_)
        return session

    async def _update_cookies(self):
        """
        Use selenium update cookies.
        """
        logger.warning(f"Will use selenium update cookies | Email: {self.user.EMAIL}")
        self.cookies, self.access_token = await asyncio.to_thread(self.sl.fetch_access_token_cookies)
        self._update_cookies_for_session(self.session)

    async def register_websocket(self, again: bool = False):
        """
        Register websocket to fetch a wss_url.
        """
        resp = None
        try:
            resp = await self.session.post(
                "https://chat.openai.com/backend-api/register-websocket",
                headers=get_headers_for_general(self.access_token),
                proxy=self.proxy
            )
            self.session.cookie_jar.update_cookies(resp.cookies)
            wss_data = await resp.json()
            logger.debug(DebugInfoMsg.RESPONSE_SUCCESS, Service.ChatWebGpt, self.user.EMAIL, wss_data)
            self.wss_url = wss_data["wss_url"]
            return wss_data["wss_url"]
        except aiohttp.ClientResponseError as e:
            if 400 <= e.status < 500:
                logger.error(ChatWebReverseErrorType.ERROR_4XX, Service.ChatWebGpt, self.user.EMAIL, e.status,
                             e.message)
                if not again:
                    if not self.sl:
                        self.sl = SeleniumRequests(self.user)
                    await self._update_cookies()
                    await self.register_websocket(again=True)
                else:
                    logger.error(ChatWebReverseErrorType.RETRY_FAILED, Service.ChatWebGpt, self.user.EMAIL,
                                 e.status)
            else:
                logger.error(ChatWebReverseErrorType.ERROR_5XX, Service.ChatWebGpt, self.user.EMAIL, e.status,
                             e.message)
                if not again:
                    await self.register_websocket(again=True)
                else:
                    logger.error(ChatWebReverseErrorType.RETRY_FAILED, Service.ChatWebGpt, self.user.EMAIL,
                                 e.status)
        except Exception as e:
            logger.exception(e)

    async def wss_client_background(self):
        """
        Demon for fetching data from websocket
        """
        while True:
            try:
                headers = get_wss_headers(self.conversation.conversation_id)
                async with self.session.ws_connect(self.wss_url,
                                                   heartbeat=20,
                                                   headers=headers) as self.wss_client:
                    logger.info("START wss_client_background")
                    data_str = None
                    async for msg in self.wss_client:

                        # logger.debug("WSMsgType: msg.type:%s\nmsg.date:↓↓↓\n%s", msg.type, msg.data)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            # if '"reconnectionToken"' in msg.data:
                            #     logger.debug(DebugInfoMsg.FETCH_SUCCESS, Service.ChatWebGpt, self.user.EMAIL, msg.data)
                            #     continue
                            if '"message_id"' in msg.data:
                                data_str = msg.data
                                continue
                            elif '"ZGF0YTogW0RPTkVdCgo="' in msg.data:
                                if not data_str:
                                    continue
                                # self.sequenceId = re.findall(r'"sequenceId":(\d+)', data_str)[0]
                                logger.debug(DebugInfoMsg.FETCH_SUCCESS, Service.ChatWebGpt, self.user.EMAIL, data_str)
                                message_data = json.loads(data_str)
                                self.conversation.current_node = message_data["data"]["message_id"]
                                message_data = base64.b64decode(message_data["data"]["body"]).decode("utf-8")
                                message_data = PATTERN_DATA.search(message_data).group(1)
                                message_data = json.loads(message_data)
                                try:
                                    self.queue.put_nowait(message_data["message"]["content"]["parts"][0])
                                except QueueFull as e:
                                    logger.error(e)
                            else:
                                continue
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            logger.debug("Fetched message from wss_client: msg.type:%s\nmsg.date:↓↓↓\n%s", msg.type,
                                         msg.data)
                            break
            except asyncio.CancelledError:
                logger.info("wss_client_background has been cancelled")
                break
            except aiohttp.ClientResponseError as e:
                logger.error(ChatWebReverseErrorType.ERROR_4XX, Service.ChatWebGpt, self.user.EMAIL, e.status,
                             e.message)
                await self.register_websocket()
            except Exception as e:
                logger.exception(e)
            await asyncio.sleep(5)

    async def _complete_conversation(self,
                                     conversation: Conversation,
                                     headers: dict,
                                     payload: dict,
                                     again: bool = False) -> str | None:
        resp = None
        try:
            if not self.queue.empty():
                logger.info('Discarded item Email %s | Text: %s↓↓↓:', self.user.EMAIL, self.queue.get_nowait())
            resp = await self.session.post(
                "https://chat.openai.com/backend-api/conversation",
                headers=headers,
                json=payload,
                proxy=self.proxy
            )
            self.session.cookie_jar.update_cookies(resp.cookies)
            resp_json = await resp.json()
            logger.debug(DebugInfoMsg.RESPONSE_SUCCESS, Service.ChatWebGpt, self.user.EMAIL, resp_json)
            if self.conversation.is_new:
                self.conversation.is_new = False
                self.conversation.is_echo = True
                self.conversation.conversation_id = resp_json["conversation_id"]
            try:
                msg = await asyncio.wait_for(self.queue.get(), 45)
                self.queue.task_done()
                logger.info(DebugInfoMsg.TRANSLATED_TEXT, Service.ChatWebGpt, self.user.EMAIL, msg)
                return msg
            except asyncio.TimeoutError:
                logger.debug(ErrorMsg.TimeOutError, Service.ChatWebGpt, self.user.EMAIL, "asyncio.queue")
                raise
        except aiohttp.ClientResponseError as e:
            if e.status >= 500:
                logger.error(ChatWebReverseErrorType.ERROR_5XX, Service.ChatWebGpt, self.user.EMAIL, e.status,
                             resp.text)
                if not again:
                    return await self._complete_conversation(conversation, headers, payload, True)
                else:
                    logger.error(ChatWebReverseErrorType.RETRY_FAILED, Service.ChatWebGpt, self.user.EMAIL,
                                 resp.status)
            else:
                raise
        except Exception as e:
            logger.error(ErrorMsg.ConnectionError, Service.ChatWebGpt, self.user.EMAIL, str(e))
            logger.exception(e)

    async def ask_web_chat(self, prompt: str, again: bool = False) -> str | None:
        """
        Prepare a conversation for asking.
        """
        con_pay_load = get_req_con_playload(prompt,
                                            self.websocket_request_id,
                                            self.conversation.conversation_id,
                                            self.conversation.current_node,
                                            str(uuid.uuid4()))
        headers = get_headers_for_conversation(self.access_token, self.conversation.conversation_id)
        try:
            text = await self._complete_conversation(self.conversation, headers, con_pay_load)
            return text
        except aiohttp.ClientResponseError as e:
            logger.error(ChatWebReverseErrorType.ERROR_4XX, Service.ChatWebGpt, self.user.EMAIL, e.status,
                         e.message)
            if not again:
                logger.info("Using Selenium | will call _complete_conversation again")
                if not self.sl:
                    self.sl = SeleniumRequests(self.user)
                await self._update_cookies()
                headers = get_headers_for_conversation(self.access_token, self.conversation.conversation_id)
                return await self._complete_conversation(self.conversation, headers, con_pay_load)
            else:
                logger.error(ChatWebReverseErrorType.RETRY_FAILED, Service.ChatWebGpt, self.user.EMAIL,
                             e.status)

    async def ask(self, paragraphs: list[str]) -> str | None:
        """
        build prompt, ask, build result.
        """
        prompt = build_prompt_web_chat_gpt(paragraphs)
        logger.info(DebugInfoMsg.PROMPT, Service.ChatWebGpt, self.user.EMAIL, prompt)
        async with self.lock:
            result = await self.ask_web_chat(prompt)
        try:
            if (resp := build_result(result, length=len(paragraphs), source=self.user.EMAIL)) is not None:
                logger.debug(DebugInfoMsg.TRANSLATED_TEXT, Service.ChatWebGpt, self.user.EMAIL, resp)
                return resp
        except UnequalParagraphCountException as e:
            logger.error(ErrorMsg.UnequalParagraphCountError, self.user.EMAIL, e.length_origin, e.length_result)
            raise


class ChatAgentPool(metaclass=SingletonMeta):
    def __init__(self, app):
        self.app = app
        self.instances = {user["EMAIL"]: ChatgptAgent(User(**user), app["client_sessions"][user["EMAIL"]])
                          for user in config.ACCOUNTS if user["USE"]}
        self.instance_list = list(self.instances.values())
        self.count = -1

    @property
    def current(self):
        if self.count < 0:
            return self.instance_list[0]
        else:
            return self.instance_list[(self.count - 1) % len(self.instance_list)]

    @property
    def next_instance(self) -> ChatgptAgent:
        self.count += 1
        return self.instance_list[self.count % len(self.instance_list)]

    async def ask(self, paragraphs: list[str]) -> list[str] | None:
        add_quotation = False
        for _ in range(len(self.instances)):
            try:
                return await self.next_instance.ask(paragraphs)
            except UnequalParagraphCountException as e:
                if len(paragraphs) == 1:
                    if not add_quotation:
                        paragraphs[0] = '&nbsp;' + paragraphs[0] + '&nbsp;'
                        add_quotation = True
                    continue
                logger.warning(f"Email:{e.source} Failed | Retry spilt paragraphs")
                task1 = None
                task2 = None
                done_email = None
                for _ in range(len(self.instances)):
                    try:
                        task1 = asyncio.create_task(self.next_instance.ask(paragraphs[0:(len(paragraphs) // 2)]))
                        done_email = self.current.user.EMAIL
                        break
                    except UnequalParagraphCountException as e:
                        raise ChatWebReverseException(
                            ErrorMsg.UnequalParagraphCountError % (e.source, e.length_origin, e.length_result))
                    except Exception as e:
                        logger.exception(e)
                for _ in range(len(self.instances)):
                    try:
                        task2 = asyncio.create_task(
                            self.next_instance.ask(paragraphs[(len(paragraphs) // 2):len(paragraphs)]))
                        done_email = done_email + ", " + self.current.user.EMAIL
                        break
                    except UnequalParagraphCountException as e:
                        raise ChatWebReverseException(
                            ErrorMsg.UnequalParagraphCountError % (e.source, e.length_origin, e.length_result))
                    except Exception as e:
                        logger.exception(e)
                result = await task1
                result += await task2
                logger.info(DebugInfoMsg.TRANSLATED_TEXT, Service.ChatWebGpt, done_email, result)
                return result
            except Exception as e:
                logger.exception(e)
        raise ChatWebReverseException(ChatWebReverseErrorType.FAILED_FATAL)

    async def close(self):
        logger.debug('Start chat agent close()')
        await asyncio.gather(*[ins.close() for ins in self.instance_list], return_exceptions=True)
