import json
import os
from datetime import datetime, timezone
from json import JSONDecodeError

from . import logger
from .exceptions import ChatWebReverseException, ChatWebReverseErrorType
from TranslateGuard.config import CONFIG_PATH
from TranslateGuard.base_exceptions import ErrorMsg
from TranslateGuard.base_message_enum import DebugInfoMsg, Service


def get_access_token(user_email: str) -> str:
    path = CONFIG_PATH / "ChatgptAuth" / f"{user_email}_accessToken.json"
    if path.exists():
        with open(path, 'r') as f:
            access_token = json.load(f)
            expires = datetime.strptime(access_token['expires'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(
                tzinfo=timezone.utc)
            if datetime.now(timezone.utc) < expires:
                return access_token["accessToken"]
            else:
                raise ChatWebReverseException(ChatWebReverseErrorType.AccessTokenExpired % user_email)
    else:
        logger.warning(ChatWebReverseErrorType.NoAccessToken, user_email, path)
        raise ChatWebReverseException(ChatWebReverseErrorType.NoAccessToken % (user_email, path))


def save_access_token(user_email: str, token_str: str):
    path = None
    try:
        path = CONFIG_PATH / "ChatgptAuth"
        if not path.exists():
            path.mkdir()
        path = path / f"{user_email}_accessToken.json"
        with open(path, 'w') as f:
            f.write(token_str)
            logger.info(DebugInfoMsg.SAVE_SUCCESS, path)
    except Exception as e:
        logger.error(ErrorMsg.SavedFailed, path, type(e))


def get_cookies(user_email: str) -> list[dict] | None:
    path = CONFIG_PATH / "ChatgptAuth" / f"{user_email}_cookies.json"
    if path.exists() and os.path.getsize(path) != 0:
        with open(path, 'r') as f:
            try:
                return json.load(f)
            except JSONDecodeError as e:
                logger.warning(ErrorMsg.MyJSONDecodeError, Service.ChatWebGpt, user_email, e.msg, e.pos, e.doc)
                raise None
    else:
        raise ChatWebReverseException(ChatWebReverseErrorType.NoCookies, user_email, path)


def save_cookies(user_email: str, cookies: list[dict]):
    path = None
    try:
        path = CONFIG_PATH / "ChatgptAuth"
        if not path.exists():
            path.mkdir()
        path = path / f"{user_email}_cookies.json"
        with open(path, 'w') as f:
            json.dump(cookies, f)
            logger.info(DebugInfoMsg.SAVE_SUCCESS, path)
    except Exception as e:
        logger.error(ErrorMsg.SavedFailed, path, e)
        raise
