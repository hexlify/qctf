# from hashlib import scrypt
from binascii import b2a_hex

from db import db, User


def find_user(login):
    return db.query(User)\
        .filter(username=login)\
        .first()


def auth_user(user, password):
    return user.password_hash == password_hash(password)


def register_user(login, password):
    user = User(username=login, password_hash=password_hash(password))
    db.add(user)
    db.save()
    return user


def password_hash(password):
    return b2a_hex(scrypt(
        password.encode(), salt=b'memoir', n=16384, r=8, p=1)).decode()
