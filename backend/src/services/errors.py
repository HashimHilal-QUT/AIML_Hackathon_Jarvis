class ProviderFailure(RuntimeError):
    """Provider call failed in a way that is eligible for fallback."""


class BusinessRuleError(RuntimeError):
    """Request was understood but cannot be executed safely."""
