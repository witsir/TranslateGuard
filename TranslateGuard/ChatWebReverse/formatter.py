from TranslateGuard.config import config


def build_prompt_web_chat_gpt(paragraphs: list[str]) -> str:
    """
    Build and define prompt
    """
    length = len(paragraphs)
    if length == 1:
        text = paragraphs[0]
        p = "text"

    else:
        text = '\n'.join([f"{num}. {para}" for num, para in enumerate(paragraphs, 1)])
        p = f"{length} paragraphs"

    user_prompt = (
        f'{config.SYSTEM_PROMPT}'
        f'Translate the following {p} into simplified Chinese. '
        f'Remember do not explain my original text, '
        f'do not generate content that is not beneficial for translation.:\n\n'
        f'{text}')
    return user_prompt
