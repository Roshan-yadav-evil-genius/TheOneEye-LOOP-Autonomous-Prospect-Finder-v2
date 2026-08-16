from typing import List
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage
import re

def get_messages_token_count_(model:BaseChatModel,messages: List[BaseMessage], known_model_total_token_count: int = 262144, SystemMessage_wrapper_token_count: int = 10) -> int:
    """Safely count exact tokens using Ollama."""
    known_chunk = SystemMessage(content="Apple"*known_model_total_token_count)
    new_msg = [known_chunk]+messages
 
    try:
        model.invoke(new_msg)
    except Exception as e:
        error_str = str(e)
        match = re.search(r"input length \((\d+) tokens\)", error_str)
 
        if match:
            return int(match.group(1))-known_model_total_token_count-SystemMessage_wrapper_token_count
 
    return 0