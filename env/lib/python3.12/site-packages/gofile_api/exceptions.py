# Invalid input from user of module
class InvalidTokenException(ValueError):
    ...


class PasswordRequiredError(ValueError):
    ...


class WrongPasswordError(ValueError):
    ...


class WrongOwnerError(ValueError):
    ...


class WrongFolderError(ValueError):
    ...


class InvalidExpirationError(ValueError):
    ...


class RequiresPremiumError(Exception):
    ...


class ContentExpiredError(Exception):
    ...


class ContentNotFoundError(Exception):
    ...


# Connection Exceptions
class RateLimitException(Exception):
    ...


class CannotReachAPIException(TimeoutError):
    ...


class UnknownResponseException(Exception):
    """sup its da module developer, i didnt bother to catch this properly. so u get this instead :)\n
    or the api has gotten an update and the program doesnt know how to understand it."""

    ...
