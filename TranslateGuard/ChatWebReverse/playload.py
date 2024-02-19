def get_req_con_playload(prompt: str,
                         websocket_request_id: str,
                         conversation_id: str | None,
                         parent_message_id: str | None,
                         message_id: str) -> dict:
    """
    Provide next conversation playload.
    """
    return {
        'action': 'next',
        'messages': [{'id': message_id,
                      'author': {'role': 'user'},
                      'content': {'content_type': 'text', 'parts': [prompt]},
                      'metadata': {}}],
        'conversation_id': conversation_id,
        'parent_message_id': parent_message_id,
        'model': 'text-davinci-002-render-sha',
        'timezone_offset_min': -480,
        'history_and_training_disabled': False,
        'suggestions': [],
        'conversation_mode': {
            'kind': 'primary_assistant',
            "plugin_ids": None
        },
        'force_paragen': False,
        'force_rate_limit': False,
        "websocket_request_id": websocket_request_id
    }


def get_continue_con_playload(conversation_id: str,
                              parent_message_id: str) -> dict:
    """
    Provide continued conversation playload.
    """
    return {'action': 'continue',
            'conversation_id': conversation_id,
            'parent_message_id': parent_message_id,
            'model': 'text-davinci-002-render-sha',
            'timezone_offset_min': -480,
            'history_and_training_disabled': False,
            "conversation_mode": {
                'kind': 'primary_assistant',
                "plugin_ids": None
            },
            }
