from abc import ABC, abstractmethod


class AbstractJwtVerifier(ABC):

    @abstractmethod
    async def verify_token(self, token: str):
        ...

    @abstractmethod
    async def get_user_id(self, token: str):
        ...