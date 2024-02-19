from TranslateGuard.base_exceptions import StrEnum


class GptTurboErrorType(StrEnum):
    GptTurboError = "Failed after 3 requests Exception"


class GptTurboException(Exception):
    def __init__(self, error_type: StrEnum, *args):
        super().__init__(error_type % args)
        self.error_type = error_type
