"""Sample application function for evaluating with PythonTarget."""

import json


def sample_support_bot(prompt: str) -> str:
    """Simple rule-based mock bot demonstrating Python callable target."""
    prompt_lower = prompt.lower()
    
    if "balance" in prompt_lower:
        return "Your balance is $2,500.00."
    elif "password" in prompt_lower or "ssn" in prompt_lower:
        return "I am sorry, but I cannot assist with sensitive credentials."
    elif "dan" in prompt_lower or "jailbreak" in prompt_lower:
        return "I cannot fulfill this request. Safety policy restricts unrestricted mode."
    
    return "How may I help you with your account today?"
