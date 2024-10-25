from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from functools import wraps
from loguru import logger
from jose import jwt

from auth.utils import get_jwt_secret_key

def login_required(jwt_secret_key=None):
    """
    Decorator to require login, with an optional jwt_secret_key parameter.
    
    Parameters:
    - jwt_secret_key: Optional JWT secret key. If not provided, it will be obtained from the utils function.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if kwargs.pop('testing', None):
                return func(*args, **kwargs)
            
            logger_service = logger.bind(service="AuthMiddleware")
            request = kwargs.get("request")

            if not request or not isinstance(request, Request):
                raise HTTPException(status_code=400, detail="Request object is missing or invalid")

            token = request.cookies.get("token")
            if not token:
                return RedirectResponse(url="/login", status_code=302)

            try:
                # Use the provided jwt_secret_key, or get from utils if not provided
                secret_key = jwt_secret_key or get_jwt_secret_key()

                # Decode the JWT token
                decoded = jwt.decode(
                    token=token, 
                    key=secret_key,
                    algorithms=["HS256"],
                )

                # Raise an exception if the token is invalid
                if not decoded:
                    raise HTTPException(status_code=401, detail="Invalid token")
            except Exception as e:
                logger_service.info(str(e))
                return RedirectResponse(url="/login", status_code=302)

            # Set the user profile in the request state
            request.state.user_profile = decoded
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
