from TranslateGuard.config import config


def get_wss_headers(device_id: str, conversation_id: str = None) -> dict:
    if conversation_id is None:
        return {
            "Origin": "https://chat.openai.com",
            "Sec-WebSocket-Protocol": "json.reliable.webpubsub.azure.v1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": config["USER_AGENT_UA"]["User-Agent"],
            'Oai-Device-Id': device_id,
            'Oai-Language': 'en-US',
            'Sec-Ch-Ua-Mobile': '?0'
        }
    else:
        return {
            "Origin": "https://chat.openai.com",
            'Referer': f'https://chat.openai.com/c/{conversation_id}',
            "Sec-WebSocket-Protocol": "json.reliable.webpubsub.azure.v1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": config["USER_AGENT_UA"]["User-Agent"],
            'Oai-Device-Id': device_id,
            'Oai-Language': 'en-US',
            'Sec-Ch-Ua-Mobile': '?0'
        }


def get_headers_for_conversation(access_token: str,
                                 device_id: str,
                                 requirements_token: str,
                                 conversation_id: str = None) -> dict:
    if conversation_id is None:
        return {
            "Origin": "https://chat.openai.com",
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'Accept': 'text/event-stream',
            'User-Agent': config["USER_AGENT_UA"]["User-Agent"],
            'Sec-Ch-Ua-Platform': "macOS",
            'Sec-Ch-Ua': config["USER_AGENT_UA"]["Sec-Ch-Ua"],
            'Oai-Device-Id': device_id,
            'Oai-Language': 'en-US',
            'Openai-Sentinel-Chat-Requirements-Token': requirements_token,
            'Sec-Ch-Ua-Mobile': '?0'
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
            'Sec-Ch-Ua': config["USER_AGENT_UA"]["Sec-Ch-Ua"],
            'Oai-Device-Id': device_id,
            'Oai-Language': 'en-US',
            'Openai-Sentinel-Chat-Requirements-Token': requirements_token,
            'Sec-Ch-Ua-Mobile': '?0'
        }


def get_headers_for_del_conversation(access_token: str, conversation_id: str) -> dict:
    return {
        'Origin': 'https://chat.openai.com',
        'Referer': f'https://chat.openai.com/',
        'Content-Type': 'application/json',
        'Accept': "*/*",
        'Authorization': f'Bearer {access_token}',
        'User-Agent': config["USER_AGENT_UA"]["User-Agent"],
        'Sec-Ch-Ua-Platform': "macOS",
        'Sec-Ch-Ua': config["USER_AGENT_UA"]["Sec-Ch-Ua"]
    }


def get_headers_for_general(access_token: str, device_id: str) -> dict:
    return {
        'Origin': 'https://chat.openai.com',
        'Referer': f'https://chat.openai.com/',
        'Content-Type': 'application/json',
        'Accept': "*/*",
        'Authorization': f'Bearer {access_token}',
        'User-Agent': config["USER_AGENT_UA"]["User-Agent"],
        'Sec-Ch-Ua-Platform': '"macOS"',
        'Sec-Ch-Ua': config["USER_AGENT_UA"]["Sec-Ch-Ua"],
        'Oai-Device-Id': device_id,
        'Oai-Language': 'en-US',
        'Sec-Ch-Ua-Mobile': '?0'
    }


def get_headers_for_openai() -> dict:
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'User-Agent': config["USER_AGENT_UA"]["User-Agent"],
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Ch-Ua-Platform': '"macOS"',
        'Sec-Ch-Ua': config["USER_AGENT_UA"]["Sec-Ch-Ua"],
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': "1"
    }
