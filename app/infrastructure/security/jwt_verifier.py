import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from loguru import logger

from app.application.interfaces.jwt_verifier import AbstractJwtVerifier
from app.infrastructure.config.config import Config


jwt_config = Config(".env")



class JWTTokenVerifier(AbstractJwtVerifier):
    def __init__(self):
        self.secret_key = jwt_config.jwt.JWT_SECRET
        self.algorithm = jwt_config.jwt.JWT_ALGORITHM


    def verify_token(self, token: str):
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"require_iat": True, "require_sub": True},
            )
            logger.info(f"Payload: {payload}")
        except ExpiredSignatureError:
            raise Exception("Токен истёк")
        except InvalidTokenError:
            raise Exception("Невалидный токен")
        return payload
    
    def get_user_id(self, token: str):
        logger.info(f"Token: {token}")
        payload = self.verify_token(token)
        return payload["sub"]