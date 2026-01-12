"""翻译相关的异常定义"""


class TranslationError(Exception):
    """翻译错误基类"""
    pass


class APIError(TranslationError):
    """API调用错误"""
    
    def __init__(self, message: str, status_code: int | None = None, provider: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.provider = provider


class LanguageNotSupportedError(TranslationError):
    """不支持的语言"""
    
    def __init__(self, language: str, provider: str | None = None):
        message = f"Language '{language}' is not supported"
        if provider:
            message += f" by {provider}"
        super().__init__(message)
        self.language = language
        self.provider = provider


class CacheError(TranslationError):
    """缓存错误"""
    pass


class ConfigurationError(TranslationError):
    """配置错误"""
    pass


class RateLimitError(APIError):
    """API速率限制错误"""
    pass


class AuthenticationError(APIError):
    """API认证错误"""
    pass
