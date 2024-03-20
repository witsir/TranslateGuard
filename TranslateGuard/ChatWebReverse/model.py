import uuid
from dataclasses import dataclass
from collections import namedtuple

User = namedtuple('User', ['EMAIL', 'PASSWORD', 'USE'])


@dataclass
class Conversation:
    user: User
    is_echo: bool = False
    is_new: bool = True
    conversation_id: str | None = None
    current_node: str = str(uuid.uuid4())
    requirements_token: str | None = None
