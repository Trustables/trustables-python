from enum import StrEnum


class Environment(StrEnum):
    """Verification environments; selection does not provision organisation access."""
    SIMULATOR = 'simulator'
    SANDBOX = 'sandbox'
    PRODUCTION = 'production'
