from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from functools import wraps
from loguru import logger
from jose import jwt

def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if kwargs.pop('testing', None):
            return func(*args, **kwargs)
        
        logger_service = logger.bind(service="AuthMiddleware")
        request = kwargs.get("request")

        token = request.cookies.get("token")
        if not token:
            return RedirectResponse(url="/login", status_code=302)

        try:
            jwt_secret_key = kwargs.pop('jwt_secret_key', None)
            if jwt_secret_key is None:
                jwt_secret_key = "secret_key_test"
            decoded = jwt.decode(
                token=token, 
                key=jwt_secret_key,
                algorithms=["HS256"],
            )
            if not decoded:
                raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger_service.info(str(e))
            return RedirectResponse(url="/login", status_code=302)

        request.state.user_profile = decoded
        return func(*args, **kwargs)
    
    return wrapper
