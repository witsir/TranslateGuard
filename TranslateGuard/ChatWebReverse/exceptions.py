from TranslateGuard.base_exceptions import StrEnum


class ChatWebReverseErrorType(StrEnum):
    NoCookies = "No Cookies or file found | Email: %s | Supposed to be in %s"
    NoAccessToken = "No AccessToken or file found | Email: %s | Supposed to be in %s"
    AccessTokenExpired = "Access Token Expired | Email %s"
    AuthenticationTokenExpired = "Authentication Token Expired | Email: %s"
    HandleCloudflareFailed = "Handle Cloudflare Failed | Email %s"
    SELENIUM_TIMEOUT = "SELENIUM_TIMEOUT: Service %s | Email %s | ELEMENT %s"
    InValidJSON = "Invalid JSON | Service %s | Email %s JSON TEXT:↓↓↓\n%s"
    ERROR_5XX = "ERROR_5XX: Service %s | Email %s | STATUS_CODE %s | TEXT:↓↓↓\n%s"
    ERROR_4XX = "ERROR_4XX: Service %s | Email %s | STATUS_CODE %s | TEXT:↓↓↓\n%s"
    RETRY_FAILED = "RETRY_FAILED: Service %s | Email %s | Previous STATUS_CODE %s"
    FAILED_FATAL = "FAILED_FATAL | The remote server may block you or another adverse event could occur."


class ChatWebReverseException(Exception):
    def __init__(self, error_type: StrEnum, *args):
        super().__init__(error_type % args)
        self.error_type = error_type
