from passlib.hash import pbkdf2_sha512
def hash_input(password):
    return pbkdf2_sha512.hash(password)

def check_hash(password, hashed):
    return pbkdf2_sha512.verify(password, hashed)