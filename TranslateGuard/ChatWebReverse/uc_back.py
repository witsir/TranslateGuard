import json
import re
import time
from pathlib import Path

import undetected_chromedriver as uc
from selenium.common import UnableToSetCookieException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from TranslateGuard.config import CONFIG_PATH
from TranslateGuard.ChatWebReverse.auth_handler import save_access_token, save_cookies, get_cookies
from TranslateGuard.config import config
from . import logger
from .exceptions import ChatWebReverseErrorType
from ..base_message_enum import DebugInfoMsg, Service


def _get_driver_executable_path():
    driver_executable_path = Path(config.DRIVER_EXECUTABLE_PATH)
    return driver_executable_path if driver_executable_path.exists() else None


class SeleniumRequests:
    def __init__(self,
                 user,
                 headless=True):
        self.headless = headless
        self.has_login_before = False
        self._driver = uc.Chrome(
            driver_executable_path=_get_driver_executable_path(),
            headless=headless)
        self.user = user
        self._wait35 = WebDriverWait(self.driver, 45)

    @property
    def driver(self):
        if not self._driver:
            self._driver = uc.Chrome(
                driver_executable_path=_get_driver_executable_path(),
                headless=self.headless)
            return self._driver
        else:
            return self._driver

    def _get_user_agent_ua(self):
        """
        Create or update a User_agent_ua.in file.
        """
        sec_ch_ua = self.driver.execute_script("return navigator.userAgentData.toJSON();")
        user_agent = self.driver.execute_script("return navigator.userAgent;")
        user_agent_ua = {
            "version_main": self.driver.capabilities['browserVersion'].split(".")[0],
            "Sec-Ch-Ua": ", ".join(
                f'"{sec_ch_ua["brands"][i]["brand"]}";v="{sec_ch_ua["brands"][i]["version"]}"' for i in
                range(len(sec_ch_ua["brands"]))),
            "User-Agent": user_agent}
        logger.info(f"success in getting user_agent_ua\n{user_agent_ua}")
        path = CONFIG_PATH / "user_agent_ua.in"
        with open(path, "w") as f:
            f.write(user_agent_ua["version_main"] + "\n")
            f.write(user_agent_ua["User-Agent"] + "\n")
            f.write(user_agent_ua["Sec-Ch-Ua"])
        return user_agent_ua

    # noinspection PyTestUnpassedFixture
    def fetch_access_token_cookies(self) -> tuple[list[dict], str, str]:
        """
        Fetches the cookies and access_token(auth_again = true) from /api/auth/session.
        """
        device_id = self.chatgpt_login_with_cookies()
        self.driver.get(f"https://chat.openai.com/api/auth/session")
        cookies = self.driver.get_cookies()
        save_cookies(self.user.EMAIL, cookies)
        json_text = self.driver.find_element(By.TAG_NAME, 'pre').text
        logger.info(DebugInfoMsg.FETCH_SUCCESS, Service.ChatWebGpt, self.user.EMAIL, json_text)
        save_access_token(self.user.EMAIL, json_text)
        self.driver.quit()
        self._driver = None
        return cookies, json.loads(json_text)["accessToken"], device_id

    def chatgpt_login_with_cookies(self, headless: bool = True) -> str:
        """
        Login to chat.openai.com with cookies.
        """
        if headless:
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride',
                                        {'userAgent': config["USER_AGENT_UA"]["User-Agent"]})
        cookies_ = get_cookies(self.user.EMAIL)
        self.driver.get('https://chat.openai.com')
        # Correct the inconsistent sameSite value exported by the EditThisCookie extension.
        for cookie in cookies_:
            try:
                cookie["sameSite"] = "None"
                self.driver.add_cookie(cookie)
            except (UnableToSetCookieException, AssertionError) as e:
                logger.warning(f"{e.msg if type(e) is UnableToSetCookieException else str(e)} {cookie['name']}")
        self.driver.get('https://chat.openai.com')
        if headless:
            try:
                if self._wait35.until(lambda x: x.find_element(By.XPATH, '//textarea[@id="prompt-textarea"]')):
                    text = self.driver.page_source
                    match = re.search(r'"DeviceId":\s*"([^"]*)"', text)
                    if match:
                        device_id = match.group(1)
                        logger.debug(f"XXXXXXXXXXXXXXXDeviceId: {device_id}")
                        return device_id
            except TimeoutException:
                logger.error(ChatWebReverseErrorType.SELENIUM_TIMEOUT,
                             Service.ChatWebGpt,
                             self.user.EMAIL,
                             '//textarea[@id="prompt-textarea"]')
                self._driver.quit()
                self._driver = uc.Chrome(
                    driver_executable_path=_get_driver_executable_path(),
                    headless=False)
                return self.chatgpt_login_with_cookies(False)
        while True:
            try:
                if self._wait35.until(lambda x: x.find_element(By.XPATH, '//textarea[@id="prompt-textarea"]')):
                    text = self.driver.page_source
                    match = re.search(r'"DeviceId":\s*"([^"]*)"', text)
                    if match:
                        device_id = match.group(1)
                        logger.debug(f"XXXXXXXXXXXXXXXDeviceId: {device_id}")
                        return device_id
            except Exception as e:
                logger.error(e)
