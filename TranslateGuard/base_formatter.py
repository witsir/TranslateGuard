import asyncio
import json
import logging
import random
import re
import string
import time
from typing import Union

from .ChatWebReverse.exceptions import ChatWebReverseException
from .config import config
from .base_exceptions import UnequalParagraphCountException, ErrorMsg

logger = logging.getLogger(__name__)

# Parse 1. 2. 3. ..., before each paragraph
PATTERN_HAS_EXTRA_NUMBER = re.compile(r'^(\d+\.\s*)', re.MULTILINE)
# Parse if it has 1. 2. 3. ..., before each paragraph
PATTERN_PARAGRAPH = re.compile(r'^\d+\.\s*(.+)', re.MULTILINE)
# Parse if wrapped in p tags
PATTERN_P_TAGS = re.compile(r'<p>(.+)</p>')
PATTERN_NEW_LINE = re.compile(r'\n+')
PATTERN_SPLIT = re.compile(config.PATTERN_SPLIT)
PATTERN_B_TAG = re.compile(r"<b\d></b\d>")

PRINTABLE_SPLIT_STRING = config.PATTERN_SPLIT.replace("\n", "\\n")


def build_prompt(paragraphs: list[str], alter: str = "") -> str:
    """
    Build and define prompt
    """
    text = '\n'.join(paragraphs)
    length = len(paragraphs)
    p = "paragraphs" if length > 1 else "paragraph"
    user_prompt = (
        f'{alter}Translate the following {length} {p} '
        f'into {length} simplified Chinese {p} colloquially. '
        'Just translate, do not explain or generate unrelated content. '

        f'{text}')
    logger.debug("user_prompt is:\n%s", user_prompt)
    return user_prompt


def build_result(raw_input: str, length: int, source: str) -> Union[list[str], None]:
    """
    Build paragraphs joined by PATTERN_SPLIT.
    """
    raw_input = raw_input.strip("\n ")
    if len(PATTERN_HAS_EXTRA_NUMBER.findall(raw_input)) == length:
        paragraphs = PATTERN_PARAGRAPH.findall(raw_input)
    else:
        paragraphs = PATTERN_NEW_LINE.split(raw_input)

    if len(paragraphs) != length:
        raise UnequalParagraphCountException(length, len(paragraphs), source=source)
    else:
        return paragraphs


def response_normal_json(content: str) -> str:
    """
    Normal openai completion response.
    """
    return json.dumps({
        "id": f"chatcmpl-{''.join(random.choices(string.ascii_letters + string.digits, k=30))}",  # fake
        "object": "chat.completion",
        "created": int(time.time()),
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": content,
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 2048,  # fake
            "completion_tokens": 8192,  # fake
            "total_tokens": 10240  # fake
        }
    }, ensure_ascii=False)


def _has_b_tag(paragraph: str, num_b_tags=2) -> bool:
    """
    Check for <b0></b0> <b1></b1> <b2></b2> ... in content.
    """
    if len(PATTERN_B_TAG.findall(paragraph)) > num_b_tags:
        return True
    else:
        return False


async def hybrid_response(request, content: str) -> str:
    """
    Take turns requesting using the pool.
    """
    b_tag_list_result = None
    no_b_tag_list_result = None
    task_with_b = None
    task_without_b = None
    paragraphs = [p.strip() for p in PATTERN_SPLIT.split(content)]
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug('Split | paragraphs:↓↓↓\n%s', paragraphs)
    try:
        if b_tag_list := [(num, paragraph) for num, paragraph in enumerate(paragraphs) if _has_b_tag(paragraph)]:
            logger.info("(NUM,PARA) | <b></b>_tags(2+) | origin paragraph(s):↓↓↓\n%s", b_tag_list)
            task_with_b = asyncio.create_task(request.app["DeepLX"].ask([item[1] for item in b_tag_list]))
        if no_b_tag_list := [(num, paragraph) for num, paragraph in enumerate(paragraphs) if not _has_b_tag(paragraph)]:
            logger.info("(NUM,PARA) | origin paragraph(s):↓↓↓\n%s", no_b_tag_list)
            task_without_b = asyncio.create_task(
                request.app["chat_agent_pool"].ask([item[1] for item in no_b_tag_list]))
        if b_tag_list:
            b_tag_list_result = await task_with_b
            b_tag_list = [(piece[0], b_tag_list_result[i]) for i, piece in enumerate(b_tag_list)]
            logger.info("Translated (NUM,PARA) | b_tags  paragraph(s):↓↓↓\n%s", b_tag_list)
        if no_b_tag_list:
            no_b_tag_list_result = await task_without_b
            no_b_tag_list = [(piece[0], no_b_tag_list_result[i]) for i, piece in enumerate(no_b_tag_list)]
            logger.info("Translated (NUM,PARA) | paragraph(s):↓↓↓\n%s", no_b_tag_list)

        if not b_tag_list:
            paragraphs = no_b_tag_list_result
        elif not no_b_tag_list:
            paragraphs = b_tag_list_result
        else:
            # merge algorithm
            paragraphs = []
            i, j = 0, 0
            while (i < len(b_tag_list)) and (j < len(no_b_tag_list)):
                if b_tag_list[i][0] <= no_b_tag_list[j][0]:
                    paragraphs.append(b_tag_list[i][1])
                    i += 1
                else:
                    paragraphs.append(no_b_tag_list[j][1])
                    j += 1
            paragraphs += [paragraph for _, paragraph in b_tag_list[i:]]
            paragraphs += [paragraph for _, paragraph in no_b_tag_list[j:]]
        logger.debug("Merged translated paragraph(s):↓↓↓\n%s", paragraphs)
        return response_normal_json(config.PATTERN_SPLIT.join(paragraphs))
    except ChatWebReverseException as e:
        if e.error_type == ErrorMsg.UnequalParagraphCountError:
            return '{"ERROR":"UnequalParagraphCountError"}'
        logger.error(e)
        return '{"ERROR":"FATAL"}'
