from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# def hash_password(password: str):
#     return pwd_context.hash(password)

# def verify_password(raw, hashed):
#     return pwd_context.verify(raw, hashed)

# from passlib.context import CryptContext

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# def hash_password(password: str):
#     return pwd_context.hash(password[:72])

# def verify_password(plain_password, hashed_password):
#     return pwd_context.verify(plain_password[:72], hashed_password)


from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
