from jose import JWTError, jwt
import os
import dotenv
from datetime import datetime

dotenv.load_dotenv()
token_encryption_key = os.getenv("TOKEN_ENCRYPTION_KEY")#TOKEN_ENCRYPTION_KEY=your_encryption_key

def create_token(username, token_duration): #token = encoded(username, datetime) token_duration in minutes
    unix_timestamp = (datetime.now() - datetime(1970, 1, 1)).total_seconds()
    ttl = token_duration * 60 + unix_timestamp
    token  = jwt.encode({'username': username, 'datetime': ttl}, token_encryption_key or '', algorithm='HS256')
    return token

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