# TEST FILE: Weak Cryptography (CWE-327)
import hashlib
import random

def hash_password(password):
    # VULNERABLE: MD5 is broken
    return hashlib.md5(password.encode()).hexdigest()

def hash_data(data):
    # VULNERABLE: SHA1 is weak
    return hashlib.sha1(data.encode()).hexdigest()

def generate_token():
    # VULNERABLE: not cryptographically secure
    return str(random.randint(100000, 999999))
