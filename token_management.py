from jose import JWTError, jwt
import os
import dotenv
import datetime

from pycparser.ply.yacc import token

dotenv.load_dotenv()
token_encryption_key = "TOKEN_ENCR"

def generate_token(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)  # Use timezone-aware UTC datetime
    }
    return jwt.encode(payload, token_encryption_key, algorithm="HS256")

def get_username_from_token(token): #get username from token
    decoded_token = jwt.decode(token, token_encryption_key or '', algorithms=['HS256'])
    return decoded_token['username']

def check_token(token): #check if token is valid and not expired
    try:
        decoded_token = jwt.decode(token, token_encryption_key or '', algorithms=['HS256'])
        current_time = datetime.utcnow().timestamp()
        if decoded_token['datetime'] < current_time:
            return False
        else:
            return True
    except Exception:
        return False