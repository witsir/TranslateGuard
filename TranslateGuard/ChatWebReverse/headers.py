from TranslateGuard.config import config


def get_wss_headers(conversation_id: str = None) -> dict:
    if conversation_id is None:
        return {
            "Origin": "https://chat.openai.com",
            "Sec-WebSocket-Protocol": "json.reliable.webpubsub.azure.v1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": config["USER_AGENT_UA"]["User-Agent"]
        }
    else:
        return {
            "Origin": "https://chat.openai.com",
            'Referer': f'https://chat.openai.com/c/{conversation_id}',
            "Sec-WebSocket-Protocol": "json.reliable.webpubsub.azure.v1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": config["USER_AGENT_UA"]["User-Agent"]
        }


def get_headers_for_conversation(access_token: str, conversation_id: str = None) -> dict:
    if conversation_id is None:
        return {
            "Origin": "https://chat.openai.com",
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'Accept': 'text/event-stream',
            'User-Agent': config["USER_AGENT_UA"]["User-Agent"],
            'Sec-Ch-Ua-Platform': "macOS",
            'Sec-Ch-Ua': config["USER_AGENT_UA"]["Sec-Ch-Ua"]
        }
    else:
        return {
            "Origin": "https://chat.openai.com",
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'Accept': 'text/event-stream',
            'Referer': f'https://chat.openai.com/c/{conversation_id}',
            'User-Agent': config["USER_AGENT_UA"]["User-Agent"],
            'Sec-Ch-Ua-Platform': "macOS",
            'Sec-Ch-Ua': config["USER_AGENT_UA"]["Sec-Ch-Ua"]
        }


def get_headers_for_del_conversation(access_token: str, conversation_id: str) -> dict:
    return {
        'Origin': 'https://chat.openai.com',
        'Referer': f'https://chat.openai.com/c/{conversation_id}',
        'Content-Type': 'application/json',
        'Accept': "*/*",
        'Authorization': f'Bearer {access_token}',
        'User-Agent': config["USER_AGENT_UA"]["User-Agent"],
        'Sec-Ch-Ua-Platform': "macOS",
        'Sec-Ch-Ua': config["USER_AGENT_UA"]["Sec-Ch-Ua"]
    }


def get_headers_for_general(access_token: str) -> dict:
    return {
        'Origin': 'https://chat.openai.com',
        'Content-Type': 'application/json',
        'Accept': "*/*",
        'Authorization': f'Bearer {access_token}',
        'User-Agent': config["USER_AGENT_UA"]["User-Agent"],
        'Sec-Ch-Ua-Platform': "macOS",
        'Sec-Ch-Ua': config["USER_AGENT_UA"]["Sec-Ch-Ua"]
    }
