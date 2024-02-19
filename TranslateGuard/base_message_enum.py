from .base_exceptions import StrEnum


class Service(StrEnum):
    GptTurbo = "GPT-Turbo"
    ChatWebGpt = "ChatWebGpt"
    Gemini = "Gemini"
    DeeplX = "DeeplX"


class DebugInfoMsg(StrEnum):
    SAVE_SUCCESS = "Save Success: File: %s"
    FETCH_SUCCESS = "Fetch Success: Service: %s | Source: %s | JSON Text:↓↓↓\n%s"
    RESPONSE_SUCCESS = "Response Success: Service: %s | Source: %s | JSON Text:↓↓↓\n%s"
    TRANSLATED_TEXT = "Translated text: Service: %s | Source: %s | Paragraphs:↓↓↓\n%s"
    REQUEST_TEXT = "To Translate text: Service: %s | Source: %s | Paragraphs:↓↓↓\n%s"
    PROMPT = "To Translate text: Service: %s | Source: %s | Prompt is:↓↓↓\n%s"
    RETRY = "RETRY: Service: % | Source: %s Why: %s"
