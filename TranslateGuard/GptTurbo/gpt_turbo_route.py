import json
import threading
from collections import namedtuple
from typing import Union

import requests
from certifi import where

from TranslateGuard.base_exceptions import UnequalParagraphCountException, ErrorMsg
from TranslateGuard.base_formatter import build_result
from TranslateGuard.base_message_enum import DebugInfoMsg, Service
from TranslateGuard.config import config
from TranslateGuard.utils import SingletonMeta
from . import logger
from .exceptions import GptTurboException, GptTurboErrorType
from .formatter import build_prompt_gpt_turbo

Api_Key = namedtuple("Api_Key", ("URL", "KEY", "NEED_PROXY", "USE"))


class RouteOpenai:
    def __init__(self, api_key: dict):
        self.api_key = Api_Key(**api_key)
        self.headers = {"Authorization": f"Bearer {self.api_key.KEY}",
                        "Content-Type": "application/json"}
        self.session = requests.Session()
        if self.api_key.NEED_PROXY:
            self.session.proxies.update({'http': "socks5://127.0.0.1:7890", 'https': "socks5://127.0.0.1:7890"})

    def ask_gpt_turbo(self, prompt: str) -> dict | None:
        """
        Standard call to OpenAI or Route API endpoint .
        """
        resp = None
        try:
            resp = self.session.post(
                self.api_key.URL,
                headers=self.headers,
                data=json.dumps(
                    {
                        "model": "gpt-3.5-turbo",
                        "messages": [{"role": "system", "content": config.SYSTEM_PROMPT},
                                     {"role": "user", "content": prompt}],
                        "temperature": 1
                    }),
                stream=False,
                verify=where(),
                timeout=15
            )
            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.HTTPError as e:
            logger.error(ErrorMsg.HttpError, Service.GptTurbo, self.api_key.URL, resp.status_code, resp.text[:80])
            raise e
        except requests.exceptions.Timeout as e:
            logger.error(ErrorMsg.TimeOutError, Service.GptTurbo, self.api_key.URL, "post")
            raise e
        except requests.exceptions.JSONDecodeError as e:
            logger.error(ErrorMsg.MyJSONDecodeError, Service.GptTurbo, self.api_key.URL, "", "", resp.text)
            raise e
        except Exception as e:
            logger.error(ErrorMsg.UnhandledError, Service.GptTurbo, self.api_key.URL, e)
            raise GptTurboException(ErrorMsg.UnhandledError, Service.GptTurbo, self.api_key.URL, e)

    def close(self):
        self.session.close()

    def ask(self, paragraphs: list[str]) -> Union[list[str], None]:
        prompt = build_prompt_gpt_turbo(paragraphs)
        try:
            result_dict = self.ask_gpt_turbo(prompt)
            logger.debug(DebugInfoMsg.RESPONSE_SUCCESS, Service.GptTurbo, self.api_key.URL, result_dict)
            if (resp := build_result(result_dict["choices"][0]["message"]["content"],
                                     length=len(paragraphs),source=self.api_key.URL)) is not None:
                logger.info(DebugInfoMsg.TRANSLATED_TEXT, Service.GptTurbo, self.api_key.URL, resp)
                return resp
        except UnequalParagraphCountException as e:
            logger.error(ErrorMsg.UnequalParagraphCountError, self.api_key.URL, e.length_origin, e.length_result)
            return None
        except Exception:
            raise


class OpenaiRoutePool(metaclass=SingletonMeta):
    def __init__(self):
        self.instances = [RouteOpenai(api_key) for api_key in config.API_KEYS if api_key["USE"]]
        self.count = -1

    @property
    def current(self):
        return self.instances[self.count]

    @property
    def next_instance(self) -> RouteOpenai:
        self.count += 1
        return self.instances[(self.count-1) % len(self.instances)]

    def ask(self, paragraphs: list[str]) -> list[str] | None:

        for _ in range(2):
            try:
                if result := self.next_instance.ask(paragraphs):
                    return result
                elif len(paragraphs) >= 2:
                    # The previous api_key failed, try to use next api_key.
                    break
                else:
                    continue
            except Exception as e:
                logger.error(e)
                continue
        if not len(paragraphs) >= 2:
            raise GptTurboException(GptTurboErrorType.GptTurboError)
        logger.warning(f"Retry spilt paragraphs, ask again")
        while True:
            try:
                if result := self.next_instance.ask(
                        paragraphs[0:(len(paragraphs) // 2)]):
                    break
            except Exception as e:
                logger.error(e)
        while True:
            try:
                if result_part := self.next_instance.ask(
                        paragraphs[(len(paragraphs) // 2):len(paragraphs)]):
                    break
            except Exception as e:
                logger.error(e)
        result += result_part
        logger.debug(DebugInfoMsg.TRANSLATED_TEXT, Service.GptTurbo, self.next_instance.api_key.URL, result)
        return result

    def close(self):
        ths = [threading.Thread(target=ins.close) for ins in self.instances]
        for th in ths:
            th.start()
        for th in ths:
            th.join()
