import json
import logging
import random
import time

import aiohttp
import requests

from TranslateGuard.base_formatter import PATTERN_NEW_LINE
from TranslateGuard.base_message_enum import DebugInfoMsg, Service
from TranslateGuard.config import config

logger = logging.getLogger(__name__)


class DeepLXLocal:
    def __init__(self, url="https://www2.deepl.com/jsonrpc", need_proxy=False) -> None:
        self.url = url
        self.session = requests.Session()
        if need_proxy:
            self.session.proxies.update({'http': "socks5://127.0.0.1:7890", 'https': "socks5://127.0.0.1:7890"})
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "x-app-os-name": "iOS",
            "x-app-os-version": "16.3.0",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "x-app-device": "iPhone13,2",
            "User-Agent": "DeepL-iOS/2.9.1 iOS 16.3.0 (iPhone13,2)",
            "x-app-build": "510265",
            "x-app-version": "2.9.1",
            "Connection": "keep-alive",
        }

    @staticmethod
    def getICount(translate_text) -> int:
        return translate_text.count("i")

    @staticmethod
    def getRandomNumber() -> int:
        random.seed(time.time())
        num = random.randint(8300000, 8399998)
        return num * 1000

    @staticmethod
    def getTimestamp(i_count: int) -> int:
        ts = int(time.time() * 1000)

        if i_count == 0:
            return ts

        i_count += 1
        return ts - ts % i_count + i_count

    def ask(self, text):
        i_count = self.getICount(text)
        id_ = self.getRandomNumber()

        post_data_str = json.dumps({
            "jsonrpc": "2.0",
            "method": "LMT_handle_texts",
            "id": id_,
            "params": {
                "texts": [{"text": text, "requestAlternatives": 0}],
                "splitting": "newlines",
                "lang": {
                    "source_lang_user_selected": "auto",
                    "target_lang": "ZH",
                },
                "timestamp": self.getTimestamp(i_count),
                "commonJobParams": {
                    "wasSpoken": False,
                    "transcribe_as": "",
                },
            },
        }, ensure_ascii=False)

        if (id_ + 5) % 29 == 0 or (id_ + 3) % 13 == 0:
            post_data_str = post_data_str.replace('"method":"', '"method" : "', -1)
        else:
            post_data_str = post_data_str.replace('"method":"', '"method": "', -1)

            # Add proxy (e.g. proxies='socks5://127.0.0.1:7890')
            try:
                resp = self.session.post(url=self.url, data=post_data_str, headers=self.headers)
                resp.raise_for_status()
                resp_text = resp.text
                resp_json = json.loads(resp_text)

                target_text = resp_json["result"]["texts"][0]["text"]
                logger.debug(target_text)

                return target_text
            except Exception as e:
                logger.error(e)

    def close(self):
        self.session.close()


class DeeplX:
    def __init__(self, url: str, session: aiohttp.ClientSession):
        self.url = url
        self.session = session
        self.headers = {
            "Content-Type": "application/json"}

    async def ask(self, text):
        logger.debug(DebugInfoMsg.REQUEST_TEXT, Service.DeeplX, self.url, text)
        try:
            resp = await self.session.post(
                url=self.url,
                headers=self.headers,
                json={
                    "text": text,
                    "source_lang": "EN",
                    "target_lang": "ZH"
                }
            )
            resp = await resp.json()
            logger.debug(DebugInfoMsg.RESPONSE_SUCCESS, Service.DeeplX, self.url, resp)
            return resp["data"]
        except Exception as e:
            logger.exception(e)


class DeepLXPool:
    def __init__(self, app):
        self.app = app
        emails = [user["EMAIL"] for user in config.ACCOUNTS if user["USE"]]
        self.instance_list = [DeeplX("http://localhost:1188/translate",
                                     app["client_sessions"][emails[0]]),
                              DeeplX("https://service-7t4cydvz-1301824650.sh.tencentapigw.com/translate",
                                     app["client_sessions"][emails[len(emails) - 1]])]
        self.count = -1

    @property
    def current(self) -> DeeplX:
        if self.count < 0:
            return self.instance_list[0]
        else:
            return self.instance_list[self.count % len(self.instance_list)]

    @property
    def next_instance(self) -> DeeplX:
        self.count += 1
        return self.instance_list[self.count % len(self.instance_list)]

    async def ask(self, paragraphs: list[str]) -> list[str] | None:
        text = "\n".join(paragraphs)
        logger.info(DebugInfoMsg.REQUEST_TEXT, Service.DeeplX, self.next_instance.url, text)
        try:
            result = await self.next_instance.ask(text)
        except aiohttp.ClientResponseError as e:
            logger.error(e)
            result = await self.next_instance.ask(text)
        return PATTERN_NEW_LINE.split(result)
