from fastapi import Depends, HTTPException, Security
from jwt import InvalidTokenError, ExpiredSignatureError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.application.interfaces.jwt_verifier import AbstractJwtVerifier


bearer_scheme = HTTPBearer()

def token_verifier():
    raise NotImplementedError("Должен быть переопределён в инфра слое ")

async def book_protocol():
    raise NotImplementedError("Должен быть переопределён в инфра слое ")

async def chapter_protocol():
    raise NotImplementedError("Должен быть переопределён в инфра слое ")

async def get_current_user(
    token: HTTPAuthorizationCredentials = Security(bearer_scheme),
    token_verifier: AbstractJwtVerifier = Depends(token_verifier)
):
    jwt_token = token.credentials
    try:
        user_id = token_verifier.get_user_id(jwt_token)
        return user_id
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Токен истёк",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Токен не валидный",
            headers={"WWW-Authenticate": "Bearer"}
        )