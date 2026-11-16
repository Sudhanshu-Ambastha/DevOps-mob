class AIProviderError(Exception):
    code="ai_error"
    http_status=502

    def __init__(self, message:str, provider:str="", retry_after:int|None=None):
        super().__init__(message)
        self.message=message
        self.provider=provider
        self.retry_after=retry_after


class ProviderNotConfigured(AIProviderError):
    code="ai_not_configured"
    http_status=503


class ProviderDisabled(AIProviderError):
    code="ai_disabled"
    http_status=503


class ProviderAuthError(AIProviderError):
    code="ai_auth_failed"
    http_status=502


class ProviderRateLimited(AIProviderError):
    code="ai_rate_limited"
    http_status=429


class ProviderQuotaExhausted(AIProviderError):
    code="ai_quota_exhausted"
    http_status=429


class ProviderTimeout(AIProviderError):
    code="ai_timeout"
    http_status=504


class ProviderUnavailable(AIProviderError):
    code="ai_unavailable"
    http_status=503


class ProviderBadResponse(AIProviderError):
    code="ai_bad_response"
    http_status=502


class PaidEndpointBlocked(AIProviderError):
    code="ai_paid_endpoint_blocked"
    http_status=503
