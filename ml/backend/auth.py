import base64
import hashlib
import hmac
import json
import secrets
import time

SCRYPT_N=2**14
SCRYPT_R=8
SCRYPT_P=1
SALT_BYTES=16
KEY_BYTES=32


def _encode(raw:bytes)->str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _decode(text:str)->bytes:
    padding="="*(-len(text)%4)

    return base64.urlsafe_b64decode(text+padding)


def _scrypt(password:str, salt:bytes, n:int, r:int, p:int)->bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=KEY_BYTES)


def hash_password(password:str)->str:
    salt=secrets.token_bytes(SALT_BYTES)
    key=_scrypt(password, salt, SCRYPT_N, SCRYPT_R, SCRYPT_P)

    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${_encode(salt)}${_encode(key)}"


def verify_password(password:str, stored:str|None)->bool:
    if not stored:
        return False

    try:
        scheme, n, r, p, salt, key=stored.split("$")
    except ValueError:
        return False

    if scheme != "scrypt":
        return False

    candidate=_scrypt(password, _decode(salt), int(n), int(r), int(p))

    return hmac.compare_digest(candidate, _decode(key))


def _sign(payload:str, secret:str)->str:
    digest=hmac.new(secret.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).digest()

    return _encode(digest)


def create_token(user_id:str, secret:str, hours:float, now:float|None=None)->str:
    issued=now if now is not None else time.time()
    body={"sub":user_id,"exp":int(issued+hours*3600)}
    payload=_encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))

    return f"{payload}.{_sign(payload, secret)}"


def read_token(token:str, secret:str, now:float|None=None)->str|None:
    try:
        payload, signature=token.split(".")
    except ValueError:
        return None

    if not hmac.compare_digest(signature, _sign(payload, secret)):
        return None

    try:
        body=json.loads(_decode(payload))
    except (ValueError, UnicodeDecodeError):
        return None

    current=now if now is not None else time.time()

    if not isinstance(body, dict) or body.get("exp", 0) < current:
        return None

    return body.get("sub")
