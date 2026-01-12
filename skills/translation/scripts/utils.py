"""翻译工具函数"""

import hashlib
import re
from typing import Any


# ISO 639-1 语言代码映射
LANGUAGE_NAMES = {
    "en": "English",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ar": "Arabic",
    "hi": "Hindi",
    "th": "Thai",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "nl": "Dutch",
    "pl": "Polish",
    "tr": "Turkish",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "no": "Norwegian",
    "cs": "Czech",
    "hu": "Hungarian",
    "ro": "Romanian",
    "el": "Greek",
    "he": "Hebrew",
    "uk": "Ukrainian",
    "bg": "Bulgarian",
    "hr": "Croatian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "et": "Estonian",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "mt": "Maltese",
    "ga": "Irish",
    "cy": "Welsh",
    "auto": "Auto-detect",
}


def normalize_language_code(code: str) -> str:
    """
    标准化语言代码（ISO 639-1）
    
    将语言代码转换为小写，处理变体（如zh-CN -> zh）
    
    参数:
        code: 语言代码
    
    返回:
        标准化后的语言代码
    """
    if not code:
        return "auto"
    
    code = code.lower().strip()
    
    # 处理带地区代码的语言（如zh-CN, en-US）
    if "-" in code:
        base_code = code.split("-")[0]
        # 保留一些常见的地区变体映射
        if base_code in LANGUAGE_NAMES:
            return base_code
    
    # 处理常见别名
    aliases = {
        "zh-cn": "zh",
        "zh-tw": "zh",
        "zh-hans": "zh",
        "zh-hant": "zh",
        "en-us": "en",
        "en-gb": "en",
    }
    
    return aliases.get(code, code)


def get_language_name(code: str) -> str:
    """
    获取语言名称
    
    参数:
        code: 语言代码
    
    返回:
        语言名称，如果未知则返回代码本身
    """
    normalized = normalize_language_code(code)
    return LANGUAGE_NAMES.get(normalized, normalized)


def preprocess_text(text: str) -> str:
    """
    预处理文本（清理、规范化）
    
    参数:
        text: 原始文本
    
    返回:
        处理后的文本
    """
    if not text:
        return ""
    
    # 去除首尾空白
    text = text.strip()
    
    # 规范化空白字符（多个空格/换行合并）
    text = re.sub(r'\s+', ' ', text)
    
    return text


def generate_cache_key(
    text: str,
    source_lang: str,
    target_lang: str,
    **options: Any
) -> str:
    """
    生成缓存键
    
    使用文本内容、语言对和选项生成唯一的缓存键
    
    参数:
        text: 文本内容
        source_lang: 源语言
        target_lang: 目标语言
        **options: 其他选项（如果影响翻译结果）
    
    返回:
        MD5哈希值作为缓存键
    """
    # 规范化文本和语言代码
    normalized_text = preprocess_text(text)
    normalized_source = normalize_language_code(source_lang)
    normalized_target = normalize_language_code(target_lang)
    
    # 构建键字符串
    key_parts = [
        normalized_text,
        normalized_source,
        normalized_target,
    ]
    
    # 添加影响翻译结果的选项
    if options:
        # 只包含可能影响翻译结果的选项
        relevant_options = {}
        for key in ["formality", "domain", "preserve_formatting"]:
            if key in options:
                relevant_options[key] = options[key]
        
        if relevant_options:
            import json
            key_parts.append(json.dumps(relevant_options, sort_keys=True))
    
    key_string = "|".join(key_parts)
    
    # 生成MD5哈希
    return hashlib.md5(key_string.encode("utf-8")).hexdigest()


def chunk_texts(texts: list[str], chunk_size: int = 100) -> list[list[str]]:
    """
    将文本列表分块（用于大批量处理）
    
    参数:
        texts: 文本列表
        chunk_size: 每块的大小
    
    返回:
        分块后的文本列表
    """
    if not texts:
        return []
    
    chunks = []
    for i in range(0, len(texts), chunk_size):
        chunks.append(texts[i:i + chunk_size])
    
    return chunks


def validate_language_code(code: str) -> bool:
    """
    验证语言代码是否有效
    
    参数:
        code: 语言代码
    
    返回:
        是否有效
    """
    if not code:
        return False
    
    normalized = normalize_language_code(code)
    
    # 检查是否是已知语言或auto
    return normalized == "auto" or normalized in LANGUAGE_NAMES


def get_supported_languages() -> list[str]:
    """
    获取支持的语言列表
    
    返回:
        语言代码列表
    """
    return sorted([code for code in LANGUAGE_NAMES.keys() if code != "auto"])
