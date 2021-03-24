
class HydeValidationError(Exception):
    """An Exception type that holds a list of validation errors"""
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors

    def __str__(self):
        errors = [f"\t{level}: {err}" for level, err in self.errors]
        return "\n".join(errors)


class HydeError(Exception):
    pass
