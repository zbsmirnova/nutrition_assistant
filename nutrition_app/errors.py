"""Safe application failures; messages contain no foreign records or raw payloads."""


class ApplicationError(Exception):
    code = "invalid_input"


class NotFound(ApplicationError):
    code = "not_found"


class Unauthorized(ApplicationError):
    code = "unauthorized"


class Conflict(ApplicationError):
    code = "revision_conflict"


class Unsupported(ApplicationError):
    code = "unsupported"


class NumericOverflow(ApplicationError):
    pass
