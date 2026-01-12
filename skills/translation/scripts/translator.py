"""核心翻译模块"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .cache import TranslationCache, MemoryCache
from .exceptions import (
    TranslationError,
    APIError,
    LanguageNotSupportedError,
    ConfigurationError,
)
from .utils import (
    normalize_language_code,
    preprocess_text,
    validate_language_code,
)


@dataclass
class TranslationResult:
    """翻译结果"""
    text: str
    source_lang: str
    target_lang: str
    confidence: float | None = None
    cached: bool = False
    provider: str = ""
    metadata: dict[str, Any] | None = None


class TranslationProvider(ABC):
    """翻译服务提供者抽象基类"""
    
    @abstractmethod
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **options: Any
    ) -> TranslationResult:
        """执行翻译"""
        pass
    
    @abstractmethod
    def detect_language(self, text: str) -> dict[str, Any]:
        """检测语言"""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> list[str]:
        """获取支持的语言列表"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """提供者名称"""
        pass


class GoogleTranslateProvider(TranslationProvider):
    """Google Translate实现（使用googletrans库）"""
    
    def __init__(self, service_url: str | None = None):
        """
        初始化Google翻译提供者
        
        参数:
            service_url: 可选的Google翻译服务URL（用于自定义端点）
        """
        try:
            from googletrans import Translator as GoogleTranslator
            self._translator = GoogleTranslator(service_urls=[service_url] if service_url else None)
        except ImportError:
            raise ConfigurationError(
                "googletrans library not installed. "
                "Install it with: pip install googletrans==4.0.0rc1"
            )
    
    @property
    def name(self) -> str:
        return "Google Translate"
    
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **options: Any
    ) -> TranslationResult:
        """执行翻译"""
        try:
            # 规范化语言代码
            source = normalize_language_code(source_lang) if source_lang != "auto" else None
            target = normalize_language_code(target_lang)
            
            # 调用Google翻译API
            result = self._translator.translate(
                text,
                src=source,
                dest=target
            )
            
            return TranslationResult(
                text=result.text,
                source_lang=result.src or source_lang,
                target_lang=result.dest,
                confidence=None,  # googletrans不提供置信度
                provider=self.name,
                metadata={
                    "original": result.origin,
                    "pronunciation": getattr(result, "pronunciation", None),
                }
            )
        except Exception as e:
            raise APIError(f"Google Translate API error: {str(e)}", provider=self.name)
    
    def detect_language(self, text: str) -> dict[str, Any]:
        """检测语言"""
        try:
            result = self._translator.detect(text)
            return {
                "language": result.lang,
                "confidence": result.confidence,
            }
        except Exception as e:
            raise APIError(f"Language detection error: {str(e)}", provider=self.name)
    
    def get_supported_languages(self) -> list[str]:
        """获取支持的语言列表"""
        try:
            return list(self._translator.get_supported_languages())
        except Exception:
            # 返回常见语言列表
            return [
                "en", "zh", "ja", "ko", "es", "fr", "de", "it", "pt", "ru",
                "ar", "hi", "th", "vi", "id", "nl", "pl", "tr", "sv", "da"
            ]


class DeepLProvider(TranslationProvider):
    """DeepL翻译实现"""
    
    def __init__(self, api_key: str | None = None, use_free_api: bool = False):
        """
        初始化DeepL提供者
        
        参数:
            api_key: DeepL API密钥（从环境变量DEEPL_API_KEY获取，如果未提供）
            use_free_api: 是否使用免费API端点
        """
        try:
            import deepl
        except ImportError:
            raise ConfigurationError(
                "deepl library not installed. "
                "Install it with: pip install deepl"
            )
        
        api_key = api_key or os.getenv("DEEPL_API_KEY")
        if not api_key:
            raise ConfigurationError("DeepL API key not provided. Set DEEPL_API_KEY environment variable.")
        
        self._translator = deepl.Translator(api_key)
        self._use_free_api = use_free_api
    
    @property
    def name(self) -> str:
        return "DeepL"
    
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **options: Any
    ) -> TranslationResult:
        """执行翻译"""
        try:
            # DeepL使用不同的语言代码格式
            source = self._normalize_deepl_lang(source_lang) if source_lang != "auto" else None
            target = self._normalize_deepl_lang(target_lang)
            
            # DeepL选项
            formality = options.get("formality", "default")
            
            result = self._translator.translate_text(
                text,
                source_lang=source,
                target_lang=target,
                formality=formality if formality != "default" else None
            )
            
            return TranslationResult(
                text=result.text,
                source_lang=result.detected_source_lang or source_lang,
                target_lang=target,
                confidence=None,
                provider=self.name,
                metadata={
                    "detected_source_lang": result.detected_source_lang,
                }
            )
        except Exception as e:
            raise APIError(f"DeepL API error: {str(e)}", provider=self.name)
    
    def detect_language(self, text: str) -> dict[str, Any]:
        """检测语言"""
        try:
            result = self._translator.translate_text(text, target_lang="EN")
            return {
                "language": result.detected_source_lang.lower(),
                "confidence": None,  # DeepL不提供置信度
            }
        except Exception as e:
            raise APIError(f"Language detection error: {str(e)}", provider=self.name)
    
    def get_supported_languages(self) -> list[str]:
        """获取支持的语言列表"""
        try:
            languages = self._translator.get_target_languages()
            return [lang.code.lower() for lang in languages]
        except Exception:
            return ["en", "zh", "ja", "de", "fr", "es", "it", "pt", "ru", "pl"]
    
    def _normalize_deepl_lang(self, lang_code: str) -> str:
        """将ISO 639-1代码转换为DeepL格式"""
        # DeepL使用大写代码
        lang_code = normalize_language_code(lang_code).upper()
        
        # DeepL特殊映射
        deepl_map = {
            "EN": "EN",
            "ZH": "ZH",
            "JA": "JA",
            "DE": "DE",
            "FR": "FR",
            "ES": "ES",
            "IT": "IT",
            "PT": "PT",
            "RU": "RU",
            "PL": "PL",
        }
        
        return deepl_map.get(lang_code, lang_code)


class OpenAIProvider(TranslationProvider):
    """OpenAI GPT翻译实现"""
    
    def __init__(self, api_key: str | None = None, model: str = "gpt-3.5-turbo"):
        """
        初始化OpenAI提供者
        
        参数:
            api_key: OpenAI API密钥（从环境变量OPENAI_API_KEY获取，如果未提供）
            model: 使用的模型名称
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ConfigurationError(
                "openai library not installed. "
                "Install it with: pip install openai"
            )
        
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ConfigurationError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        self._client = OpenAI(api_key=api_key)
        self._model = model
    
    @property
    def name(self) -> str:
        return f"OpenAI ({self._model})"
    
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **options: Any
    ) -> TranslationResult:
        """执行翻译"""
        try:
            source_name = self._get_language_name(source_lang) if source_lang != "auto" else "the detected language"
            target_name = self._get_language_name(target_lang)
            
            prompt = f"Translate the following text from {source_name} to {target_name}. Only return the translation, no explanations:\n\n{text}"
            
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            
            translated = response.choices[0].message.content.strip()
            
            return TranslationResult(
                text=translated,
                source_lang=source_lang,
                target_lang=target_lang,
                confidence=None,
                provider=self.name,
                metadata={
                    "model": self._model,
                    "tokens": response.usage.total_tokens if hasattr(response, "usage") else None,
                }
            )
        except Exception as e:
            raise APIError(f"OpenAI API error: {str(e)}", provider=self.name)
    
    def detect_language(self, text: str) -> dict[str, Any]:
        """检测语言"""
        try:
            prompt = f"What language is the following text written in? Respond with only the ISO 639-1 language code:\n\n{text}"
            
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
            )
            
            detected_lang = response.choices[0].message.content.strip().lower()
            
            return {
                "language": detected_lang,
                "confidence": None,
            }
        except Exception as e:
            raise APIError(f"Language detection error: {str(e)}", provider=self.name)
    
    def get_supported_languages(self) -> list[str]:
        """获取支持的语言列表"""
        # OpenAI理论上支持所有语言
        return [
            "en", "zh", "ja", "ko", "es", "fr", "de", "it", "pt", "ru",
            "ar", "hi", "th", "vi", "id", "nl", "pl", "tr", "sv", "da"
        ]
    
    def _get_language_name(self, lang_code: str) -> str:
        """获取语言名称"""
        from .utils import get_language_name
        return get_language_name(lang_code)


class Translator:
    """主翻译器类，整合缓存和翻译服务"""
    
    def __init__(
        self,
        provider: TranslationProvider,
        cache: TranslationCache | None = None,
        default_source_lang: str = "auto",
        default_target_lang: str = "en"
    ):
        """
        初始化翻译器
        
        参数:
            provider: 翻译服务提供者
            cache: 缓存管理器（可选，默认使用内存缓存）
            default_source_lang: 默认源语言
            default_target_lang: 默认目标语言
        """
        self.provider = provider
        self.cache = cache or MemoryCache()
        self.default_source_lang = default_source_lang
        self.default_target_lang = default_target_lang
    
    def translate(
        self,
        text: str,
        source_lang: str | None = None,
        target_lang: str | None = None,
        use_cache: bool = True,
        **options: Any
    ) -> TranslationResult:
        """
        翻译文本（带缓存）
        
        参数:
            text: 要翻译的文本
            source_lang: 源语言（None则使用默认值）
            target_lang: 目标语言（None则使用默认值）
            use_cache: 是否使用缓存
            **options: 其他翻译选项
        
        返回:
            TranslationResult对象
        """
        if not text or not text.strip():
            return TranslationResult(
                text="",
                source_lang=source_lang or self.default_source_lang,
                target_lang=target_lang or self.default_target_lang,
                provider=self.provider.name
            )
        
        # 使用默认值
        source = source_lang if source_lang is not None else self.default_source_lang
        target = target_lang if target_lang is not None else self.default_target_lang
        
        # 验证语言代码
        if source != "auto" and not validate_language_code(source):
            raise LanguageNotSupportedError(source, self.provider.name)
        if not validate_language_code(target):
            raise LanguageNotSupportedError(target, self.provider.name)
        
        # 预处理文本
        processed_text = preprocess_text(text)
        
        # 检查缓存
        if use_cache:
            cached_result = self.cache.get(processed_text, source, target, **options)
            if cached_result is not None:
                return TranslationResult(
                    text=cached_result,
                    source_lang=source,
                    target_lang=target,
                    cached=True,
                    provider=self.provider.name
                )
        
        # 如果源语言是auto，先检测语言
        if source == "auto":
            detection = self.provider.detect_language(processed_text)
            source = detection.get("language", "en")
        
        # 调用翻译服务
        result = self.provider.translate(processed_text, source, target, **options)
        
        # 保存到缓存
        if use_cache:
            try:
                self.cache.set(processed_text, source, target, result.text, **options)
            except Exception:
                # 缓存失败不应该影响翻译结果
                pass
        
        return result
    
    def translate_batch(
        self,
        texts: list[str],
        source_lang: str | None = None,
        target_lang: str | None = None,
        use_cache: bool = True,
        parallel: bool = True,
        **options: Any
    ) -> list[TranslationResult]:
        """
        批量翻译多个文本
        
        参数:
            texts: 要翻译的文本列表
            source_lang: 源语言
            target_lang: 目标语言
            use_cache: 是否使用缓存
            parallel: 是否并行处理（默认True）
            **options: 其他翻译选项
        
        返回:
            TranslationResult列表
        """
        if not texts:
            return []
        
        # 使用默认值
        source = source_lang if source_lang is not None else self.default_source_lang
        target = target_lang if target_lang is not None else self.default_target_lang
        
        results = []
        
        # 批量检查缓存
        if use_cache:
            cached_results = {}
            uncached_indices = []
            
            for i, text in enumerate(texts):
                if not text or not text.strip():
                    results.append(TranslationResult(
                        text="",
                        source_lang=source,
                        target_lang=target,
                        provider=self.provider.name
                    ))
                    continue
                
                processed_text = preprocess_text(text)
                cached_result = self.cache.get(processed_text, source, target, **options)
                
                if cached_result is not None:
                    cached_results[i] = TranslationResult(
                        text=cached_result,
                        source_lang=source,
                        target_lang=target,
                        cached=True,
                        provider=self.provider.name
                    )
                else:
                    uncached_indices.append(i)
            
            # 填充已缓存的结果
            for i in range(len(texts)):
                if i in cached_results:
                    results.append(cached_results[i])
                else:
                    results.append(None)  # 占位符
        else:
            uncached_indices = list(range(len(texts)))
            results = [None] * len(texts)
        
        # 翻译未缓存的文本
        if uncached_indices:
            if parallel:
                # 并行翻译（简化实现，实际可以使用线程池）
                import concurrent.futures
                
                def translate_one(idx: int) -> tuple[int, TranslationResult]:
                    text = texts[idx]
                    return idx, self.translate(text, source, target, use_cache=False, **options)
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_idx = {executor.submit(translate_one, idx): idx for idx in uncached_indices}
                    for future in concurrent.futures.as_completed(future_to_idx):
                        idx, result = future.result()
                        results[idx] = result
            else:
                # 串行翻译
                for idx in uncached_indices:
                    text = texts[idx]
                    results[idx] = self.translate(text, source, target, use_cache=False, **options)
            
            # 批量保存到缓存
            if use_cache:
                for idx in uncached_indices:
                    if results[idx] and results[idx].text:
                        processed_text = preprocess_text(texts[idx])
                        try:
                            self.cache.set(
                                processed_text,
                                source,
                                target,
                                results[idx].text,
                                **options
                            )
                        except Exception:
                            pass
        
        return results
    
    def detect_language(self, text: str) -> dict[str, Any]:
        """检测语言"""
        return self.provider.detect_language(text)
    
    def get_supported_languages(self) -> list[str]:
        """获取支持的语言列表"""
        return self.provider.get_supported_languages()
