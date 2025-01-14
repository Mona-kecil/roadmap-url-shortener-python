import hashlib
import base64


def generate_short_hash(*, input_string: str, length: int = 5) -> str:
    """
    Generate a SHA256 hash of the input string and encode it in base64
    truncating it to the desired length.
    """
    hash_obj = hashlib.sha256(input_string.encode())
    base64_hash = base64.urlsafe_b64encode(hash_obj.digest()).decode()
    return base64_hash[:length]
