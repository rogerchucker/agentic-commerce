class WalletError(Exception):
    pass


class NotFoundError(WalletError):
    pass


class ConflictError(WalletError):
    pass


class ValidationError(WalletError):
    pass


class ServiceUnavailableError(WalletError):
    pass


class UnauthorizedError(WalletError):
    pass


class ForbiddenError(WalletError):
    pass
