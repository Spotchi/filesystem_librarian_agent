import json
def format_conversation(messages, exclude_role=['system'], attribute_prefix=''):
    """
    Concatenates messages in a format of role: content
    
    Args:
        messages (str): JSON string containing list of message dictionaries with 'role' and 'content' keys
        
    Returns:
        str: Formatted conversation string with each message on a new line
    """
    if isinstance(messages, str):
        messages = json.loads(messages)
    role_key = f'{attribute_prefix}role'
    content_key = f'{attribute_prefix}content'
    formatted = []
    for message in messages:
        if message[role_key] in exclude_role:
            continue
        formatted.append(f"{message[role_key]}: {message[content_key]}")
    return "\n".join(formatted)

def format_conversation_nested_message(messages, nested_message_key='message', exclude_role=['system'], attribute_prefix=''):
    """
    Concatenates messages in a format of role: content
    
    Args:
        messages (str): JSON string containing list of message dictionaries with 'role' and 'content' keys
        
    Returns:
        str: Formatted conversation string with each message on a new line
    """
    if isinstance(messages, str):
        messages = json.loads(messages)
    role_key = f'{attribute_prefix}role'
    content_key = f'{attribute_prefix}content'
    formatted = []
    for message in messages:
        role = message.get(nested_message_key, {}).get(role_key)
        content = message.get(nested_message_key, {}).get(content_key)
        if role in exclude_role:
            continue
        formatted.append(f"{role}: {content}")
    return "\n".join(formatted)

