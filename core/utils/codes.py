import secrets

def generate_registration_code(length=8):
    """
    Generates a secure, unique, and user-friendly short alphanumeric code 
    (excluding easily confused characters like I, O, 1, 0, L).
    """
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))
