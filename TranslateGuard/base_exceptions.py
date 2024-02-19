from enum import Enum


class StrEnum(str, Enum):
    def __str__(self):
        return self.value


class ErrorMsg(StrEnum):
    SavedFailed = "FATAL: File: %s saved Failed. Exception:↓↓↓ %s"
    RetryError = "Exceeded Retry max times %s | source: %s | The final Exception:↓↓↓ %s"
    MyJSONDecodeError = "JSONDecodeError! Service: %s | Source: %s | Decode Msg: %s | Error position： %s | JSON text: ↓↓↓\n%s"  # noqa
    HttpError = "HttpError! Service: %s | Source: %s | STATUS_CODE: %s | Response Content: ↓↓↓\n%s"  # noqa
    ConnectionError = "ConnectionError! | Service: %s | Source: %s got failed with a Error:↓↓↓\n%s"
    ParseError = "ParseError! Source： %s got abnormal %s response so cannot parse it into JSON"  # noqa
    KeyError = "Service: %s | Source: %s | Message:↓↓↓ %s"
    TimeOutError = "TimeOutError! Service: %s | Source: %s | Job: %s"
    UnequalParagraphCountError = "UnequalParagraphCountError! Source: %s, Exception: Need %s but received %s"  # noqa
    TooManyRequestsException = "TooManyRequestsException! Too many requests, your IP has been blocked by DeepL temporarily, please don't request it frequently in a short time." # noqa
    UnhandledError = "UnhandledError! Service: %s | Source: %s Failed, Exception:↓↓↓ %s" # noqa


class UnequalParagraphCountException(Exception):
    def __init__(self, length_origin: int, length_result: int, source: str):
        self.error_type = ErrorMsg.UnequalParagraphCountError
        self.length_origin = length_origin
        self.length_result = length_result
        self.source = source
        super().__init__(ErrorMsg.UnequalParagraphCountError)


class GeneralException(Exception):
    def __init__(self, error_type: ErrorMsg, *args):
        super().__init__(error_type % args)
        self.error_type = error_type


class RetryException(Exception):
    def __init__(self, error_type: ErrorMsg, **kwargs):
        super().__init__(error_type % kwargs)
        self.error_type = error_type


class TooManyRequestsException(Exception):
    def __init__(self, error_type: ErrorMsg=ErrorMsg.TooManyRequestsException, **kwargs):
        super().__init__(error_type % kwargs)
        self.error_type = error_type