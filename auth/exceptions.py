class NoTokenSupplied(Exception):
    def __init__(self, message="Token cannot be empty"):
        self.message = message
        super().__init__(self.message)

class InvalidToken(Exception):
    def __init__(self, message="Token is invalid"):
        self.message = message
        super().__init__(self.message)

class UserNotFound(Exception):
    def __init__(self, message="This user does not exist"):
        self.message = message
        super().__init__(self.message)

class SubNotFound(Exception):
    def __init__(self, message="Subject identifier cannot be empty"):
        self.message = message
        super().__init__(self.message)

class InvalidEmail(Exception):
    def __init__(self, message="Email cannot be empty"):
        self.message = message
        super().__init__(self.message)

class InvalidName(Exception):
    def __init__(self, message="Name cannot be empty"):
        self.message = message
        super().__init__(self.message)

class InvalidPictureURL(Exception):
    def __init__(self, message="Picture URL must be a valid HTTP/HTTPS URL"):
        self.message = message
        super().__init__(self.message)

class InvalidLoginMethod(Exception):
    def __init__(self, message="Login method is invalid"):
        self.message = message
        super().__init__(self.message)

class InvalidUUID(Exception):
    def __init__(self, message="UUID cannot be empty"):
        self.message = message
        super().__init__(self.message)
