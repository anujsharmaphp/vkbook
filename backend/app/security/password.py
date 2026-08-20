import bcrypt

_ENCODING = "utf-8"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(_ENCODING), bcrypt.gensalt()).decode(_ENCODING)


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(_ENCODING), password_hash.encode(_ENCODING))
