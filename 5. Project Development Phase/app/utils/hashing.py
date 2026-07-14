import hashlib

def sha256_ip(raw_ip: str) -> str:
    """
    Hashes a raw IP address using SHA-256 for privacy compliance.
    """
    if not raw_ip:
        return ""
    return hashlib.sha256(raw_ip.encode('utf-8')).hexdigest()
