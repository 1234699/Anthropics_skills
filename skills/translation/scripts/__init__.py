"""翻译Skill模块"""

from .cache import (
    TranslationCache,
    MemoryCache,
    FileCache,
    SQLiteCache,
    CacheStats,
)
from .exceptions import (
    TranslationError,
    APIError,
    LanguageNotSupportedError,
    CacheError,
    ConfigurationError,
    RateLimitError,
    AuthenticationError,
)
from .translator import (
    TranslationProvider,
    GoogleTranslateProvider,
    DeepLProvider,
    OpenAIProvider,
    Translator,
    TranslationResult,
)
from .batch_translator import BatchTranslator
from .utils import (
    normalize_language_code,
    get_language_name,
    preprocess_text,
    generate_cache_key,
    chunk_texts,
    validate_language_code,
    get_supported_languages,
)

__all__ = [
    # Cache
    "TranslationCache",
    "MemoryCache",
    "FileCache",
    "SQLiteCache",
    "CacheStats",
    # Exceptions
    "TranslationError",
    "APIError",
    "LanguageNotSupportedError",
    "CacheError",
    "ConfigurationError",
    "RateLimitError",
    "AuthenticationError",
    # Providers
    "TranslationProvider",
    "GoogleTranslateProvider",
    "DeepLProvider",
    "OpenAIProvider",
    # Translator
    "Translator",
    "TranslationResult",
    # Batch Translator
    "BatchTranslator",
    # Utils
    "normalize_language_code",
    "get_language_name",
    "preprocess_text",
    "generate_cache_key",
    "chunk_texts",
    "validate_language_code",
    "get_supported_languages",
]
