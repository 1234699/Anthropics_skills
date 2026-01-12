"""批量翻译工具模块"""

from typing import Any

from .translator import Translator, TranslationResult
from .utils import chunk_texts


class BatchTranslator:
    """批量翻译工具类，提供高级批量处理功能"""
    
    def __init__(self, translator: Translator):
        """
        初始化批量翻译器
        
        参数:
            translator: Translator实例
        """
        self.translator = translator
    
    def translate_batch(
        self,
        texts: list[str],
        source_lang: str | None = None,
        target_lang: str | None = None,
        use_cache: bool = True,
        parallel: bool = True,
        batch_size: int = 100,
        max_workers: int = 5,
        **options: Any
    ) -> list[TranslationResult]:
        """
        批量翻译，支持分块和并行处理
        
        参数:
            texts: 要翻译的文本列表
            source_lang: 源语言
            target_lang: 目标语言
            use_cache: 是否使用缓存
            parallel: 是否并行处理
            batch_size: 每批处理的文本数量
            max_workers: 最大并行工作线程数
            **options: 其他翻译选项
        
        返回:
            TranslationResult列表
        """
        if not texts:
            return []
        
        # 如果文本数量小于批次大小，直接处理
        if len(texts) <= batch_size:
            return self.translator.translate_batch(
                texts,
                source_lang=source_lang,
                target_lang=target_lang,
                use_cache=use_cache,
                parallel=parallel,
                **options
            )
        
        # 分块处理
        chunks = chunk_texts(texts, chunk_size=batch_size)
        all_results = []
        
        for chunk in chunks:
            chunk_results = self.translator.translate_batch(
                chunk,
                source_lang=source_lang,
                target_lang=target_lang,
                use_cache=use_cache,
                parallel=parallel,
                **options
            )
            all_results.extend(chunk_results)
        
        return all_results
    
    def translate_file(
        self,
        file_path: str,
        source_lang: str | None = None,
        target_lang: str | None = None,
        encoding: str = "utf-8",
        **options: Any
    ) -> list[TranslationResult]:
        """
        翻译文件中的文本（每行一个）
        
        参数:
            file_path: 文件路径
            source_lang: 源语言
            target_lang: 目标语言
            encoding: 文件编码
            **options: 其他翻译选项
        
        返回:
            TranslationResult列表
        """
        try:
            with open(file_path, "r", encoding=encoding) as f:
                lines = [line.strip() for line in f.readlines()]
            
            return self.translate_batch(
                lines,
                source_lang=source_lang,
                target_lang=target_lang,
                **options
            )
        except IOError as e:
            raise IOError(f"Failed to read file: {e}")
    
    def translate_dict(
        self,
        data: dict[str, Any],
        source_lang: str | None = None,
        target_lang: str | None = None,
        **options: Any
    ) -> dict[str, Any]:
        """
        翻译字典中的值（递归）
        
        参数:
            data: 要翻译的字典
            source_lang: 源语言
            target_lang: 目标语言
            **options: 其他翻译选项
        
        返回:
            翻译后的字典
        """
        result = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # 翻译字符串值
                translation = self.translator.translate(
                    value,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    **options
                )
                result[key] = translation.text
            elif isinstance(value, dict):
                # 递归翻译嵌套字典
                result[key] = self.translate_dict(
                    value,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    **options
                )
            elif isinstance(value, list):
                # 翻译列表中的字符串
                result[key] = [
                    self.translator.translate(
                        item,
                        source_lang=source_lang,
                        target_lang=target_lang,
                        **options
                    ).text if isinstance(item, str) else item
                    for item in value
                ]
            else:
                # 保持原值
                result[key] = value
        
        return result
