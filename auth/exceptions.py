class NoTokenSupplied(Exception):
    def __init__(self, message="Token cannot be empty"):
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
