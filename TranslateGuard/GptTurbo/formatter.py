from TranslateGuard.base_message_enum import DebugInfoMsg, Service
from . import logger
from ..config import config


# def build_prompt_gpt_turbo(paragraphs: list[str]) -> str:
#     """
#     Build and define prompt for Gpt turbo modle.
#     """
#     length = len(paragraphs)
#     if length == 1:
#         text = paragraphs[0]
#         p = "paragraph"
#         add_1 = ''
#         add_2 = ''
#     else:
#         p = "paragraphs"
#         text = '\n'.join(["<p>" + p + "</p>" for p in paragraphs])
#         add_1 = "The number of result paragraphs must be the same as in the original. "
#         add_2 = f'Remove the wrapped <p> tags and just provide the exactly {length} simplified Chinese {p}.'
#     user_prompt = (
#         f'{config.USER_PROMPT_ADD}'
#         f'Translate the content of the following {length} {p} (enclosed within <p> tags) '
#         f'into simplified Chinese. {add_1}'
#         'Remember do not explain my original text, '
#         f'do not generate content that is not beneficial for translation. {add_2}:\n\n'
#         f'{text}')
#     logger.debug(DebugInfoMsg.PROMPT, Service.GptTurbo, user_prompt)
#     return user_prompt
def build_prompt_gpt_turbo(paragraphs: list[str]) -> str:
    """
    Build and define prompt for Gpt turbo modle.
    """
    length = len(paragraphs)
    if length == 1:
        text = paragraphs[0]
        p = "paragraph"
        add_1 = '.'
        add_2 = ''
    else:
        p = "paragraphs"
        text = '\n'.join(paragraphs)
        add_1 = ", line by line."
        add_2 = f" Just provide the exactly {length} simplified Chinese {p}."
    user_prompt = (
        f'{config.USER_PROMPT_ADD}'
        f'Translate the following {length} {p} into simplified Chinese{add_1} '
        'Remember do not explain my original text, '
        f'do not generate content that is not beneficial for translation.{add_2}:\n\n'
        f'{text}')
    logger.debug(DebugInfoMsg.PROMPT, Service.GptTurbo, user_prompt)
    return user_prompt
