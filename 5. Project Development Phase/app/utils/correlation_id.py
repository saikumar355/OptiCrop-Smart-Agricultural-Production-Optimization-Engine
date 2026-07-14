import secrets

def generate_correlation_id() -> str:
    """
    Generates an 8-character hex token to trace requests.
    """
    return secrets.token_hex(4)
