from fastapi import Depends, Header, HTTPException, status, Request
from loguru import logger

def token_verifier():
    raise NotImplementedError("Должен быть переопределён в инфра слое ")

async def book_protocol():
    raise NotImplementedError("Должен быть переопределён в инфра слое ")

async def chapter_protocol():
    raise NotImplementedError("Должен быть переопределён в инфра слое ")

async def storage():    
    raise NotImplementedError("Должен быть переопределён в инфра слое ")

async def get_current_user(request:Request, x_user_id: str = Header(None)):
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="X-User-Id хедер потерян или не найден"
        )
    try:
        return int(x_user_id)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="X-User-Id хедер должен быть int")

async def get_check_admin(
    x_admin: str = Header(None, alias="x-user-role"), 
    x_user_id = Depends(get_current_user)):
    if x_admin != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )
    return {"x-admin": x_admin, "x-user-id": x_user_id}