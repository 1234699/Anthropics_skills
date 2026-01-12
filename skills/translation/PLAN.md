# 翻译 Skill 规划文档

## 功能需求

1. **多语言互译**：支持任意两种语言之间的翻译
2. **批量翻译**：支持一次翻译多个文本片段
3. **缓存机制**：避免重复翻译，提高效率

## 文件结构

```
translation/
├── SKILL.md                    # Skill主文档（指令和说明）
├── LICENSE.txt                 # 许可证文件
├── requirements.txt            # Python依赖（如需要）
├── scripts/                    # Python脚本目录
│   ├── __init__.py
│   ├── translator.py          # 核心翻译模块
│   ├── cache.py               # 缓存管理模块
│   └── batch_translator.py    # 批量翻译工具
├── examples/                   # 示例目录
│   ├── basic_translation.md   # 基础翻译示例
│   ├── batch_translation.md   # 批量翻译示例
│   └── cache_demo.md          # 缓存使用示例
└── README.md                   # 使用说明（可选）
```

## API 设计

### 1. 核心翻译 API

#### 1.1 单文本翻译

```python
def translate(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "en",
    use_cache: bool = True,
    **kwargs
) -> dict:
    """
    翻译单个文本
    
    参数:
        text: 要翻译的文本
        source_lang: 源语言代码（ISO 639-1），"auto"表示自动检测
        target_lang: 目标语言代码（ISO 639-1），默认"en"
        use_cache: 是否使用缓存，默认True
        **kwargs: 其他翻译选项（如formality, domain等）
    
    返回:
        {
            "text": "翻译后的文本",
            "source_lang": "检测到的源语言",
            "target_lang": "目标语言",
            "confidence": 0.95,  # 翻译置信度（可选）
            "cached": False      # 是否来自缓存
        }
    """
```

#### 1.2 批量翻译

```python
def translate_batch(
    texts: list[str],
    source_lang: str = "auto",
    target_lang: str = "en",
    use_cache: bool = True,
    parallel: bool = True,
    **kwargs
) -> list[dict]:
    """
    批量翻译多个文本
    
    参数:
        texts: 要翻译的文本列表
        source_lang: 源语言代码
        target_lang: 目标语言代码
        use_cache: 是否使用缓存
        parallel: 是否并行处理（默认True）
        **kwargs: 其他翻译选项
    
    返回:
        [
            {
                "original": "原文",
                "translated": "翻译",
                "source_lang": "源语言",
                "cached": False
            },
            ...
        ]
    """
```

#### 1.3 语言检测

```python
def detect_language(text: str) -> dict:
    """
    检测文本语言
    
    参数:
        text: 要检测的文本
    
    返回:
        {
            "language": "zh",  # ISO 639-1代码
            "confidence": 0.98,
            "alternatives": [  # 备选语言（可选）
                {"language": "ja", "confidence": 0.02}
            ]
        }
    """
```

### 2. 缓存 API

#### 2.1 缓存管理

```python
class TranslationCache:
    """
    翻译缓存管理器
    支持内存缓存和持久化缓存（文件/数据库）
    """
    
    def __init__(
        self,
        cache_type: str = "memory",  # "memory" | "file" | "sqlite"
        cache_dir: str = ".translation_cache",
        max_size: int = 10000,  # 最大缓存条目数
        ttl: int = 86400  # 缓存过期时间（秒），默认24小时
    ):
        """
        初始化缓存
        
        参数:
            cache_type: 缓存类型
            cache_dir: 缓存目录（文件/数据库模式）
            max_size: 最大缓存条目数
            ttl: 缓存生存时间（秒）
        """
    
    def get(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str | None:
        """
        从缓存获取翻译
        
        返回:
            翻译文本，如果不存在则返回None
        """
    
    def set(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translated: str
    ) -> None:
        """
        保存翻译到缓存
        """
    
    def clear(self, pattern: str | None = None) -> int:
        """
        清除缓存
        
        参数:
            pattern: 可选，匹配模式（如语言对）
        
        返回:
            清除的条目数
        """
    
    def stats(self) -> dict:
        """
        获取缓存统计信息
        
        返回:
            {
                "total_entries": 1000,
                "hits": 850,
                "misses": 150,
                "hit_rate": 0.85,
                "size_mb": 2.5
            }
        """
```

#### 2.2 缓存键生成

```python
def generate_cache_key(
    text: str,
    source_lang: str,
    target_lang: str,
    **options
) -> str:
    """
    生成缓存键
    
    使用hash确保一致性，考虑：
    - 文本内容
    - 语言对
    - 翻译选项（如果影响结果）
    
    返回:
        MD5或SHA256哈希值
    """
```

### 3. 翻译服务接口（抽象层）

```python
class TranslationProvider(ABC):
    """
    翻译服务提供者抽象基类
    支持多种翻译服务（Google Translate, DeepL, OpenAI等）
    """
    
    @abstractmethod
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **options
    ) -> dict:
        """执行翻译"""
        pass
    
    @abstractmethod
    def detect_language(self, text: str) -> dict:
        """检测语言"""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> list[str]:
        """获取支持的语言列表"""
        pass


class GoogleTranslateProvider(TranslationProvider):
    """Google Translate实现"""
    pass


class DeepLProvider(TranslationProvider):
    """DeepL实现"""
    pass


class OpenAIProvider(TranslationProvider):
    """OpenAI GPT实现"""
    pass
```

### 4. 主翻译器类

```python
class Translator:
    """
    主翻译器类，整合缓存和翻译服务
    """
    
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
            cache: 缓存管理器（可选）
            default_source_lang: 默认源语言
            default_target_lang: 默认目标语言
        """
    
    def translate(
        self,
        text: str,
        source_lang: str | None = None,
        target_lang: str | None = None,
        use_cache: bool = True,
        **options
    ) -> dict:
        """
        翻译文本（带缓存）
        """
        # 1. 检查缓存
        # 2. 如果未命中，调用provider翻译
        # 3. 保存到缓存
        # 4. 返回结果
    
    def translate_batch(
        self,
        texts: list[str],
        source_lang: str | None = None,
        target_lang: str | None = None,
        use_cache: bool = True,
        parallel: bool = True,
        **options
    ) -> list[dict]:
        """
        批量翻译（带缓存和并行处理）
        """
        # 1. 批量检查缓存
        # 2. 对未缓存的文本并行翻译
        # 3. 批量保存到缓存
        # 4. 返回结果列表
    
    def detect_language(self, text: str) -> dict:
        """检测语言"""
        return self.provider.detect_language(text)
```

### 5. 工具函数

```python
# 语言代码工具
def normalize_language_code(code: str) -> str:
    """标准化语言代码（ISO 639-1）"""
    pass


def get_language_name(code: str) -> str:
    """获取语言名称"""
    pass


# 文本预处理
def preprocess_text(text: str) -> str:
    """预处理文本（清理、规范化）"""
    pass


# 批量处理工具
def chunk_texts(texts: list[str], chunk_size: int = 100) -> list[list[str]]:
    """将文本列表分块（用于大批量处理）"""
    pass
```

## 使用示例

### 示例1：基础翻译

```python
from scripts.translator import Translator
from scripts.cache import TranslationCache
from scripts.translator import GoogleTranslateProvider

# 初始化
cache = TranslationCache(cache_type="file", cache_dir=".cache")
provider = GoogleTranslateProvider(api_key="your_key")
translator = Translator(provider=provider, cache=cache)

# 翻译
result = translator.translate(
    "你好，世界！",
    source_lang="zh",
    target_lang="en"
)
print(result["text"])  # "Hello, world!"
```

### 示例2：批量翻译

```python
texts = [
    "欢迎使用翻译服务",
    "这是一个批量翻译示例",
    "支持多种语言"
]

results = translator.translate_batch(
    texts,
    source_lang="zh",
    target_lang="en",
    parallel=True
)

for result in results:
    print(f"{result['original']} -> {result['translated']}")
```

### 示例3：缓存管理

```python
# 查看缓存统计
stats = cache.stats()
print(f"命中率: {stats['hit_rate']:.2%}")

# 清除特定语言对的缓存
cache.clear(pattern="zh-en")

# 清除所有缓存
cache.clear()
```

## 配置选项

### 环境变量

```bash
# 翻译服务API密钥
TRANSLATION_API_KEY=your_api_key
TRANSLATION_PROVIDER=google  # google | deepl | openai

# 缓存配置
TRANSLATION_CACHE_TYPE=file  # memory | file | sqlite
TRANSLATION_CACHE_DIR=.translation_cache
TRANSLATION_CACHE_TTL=86400  # 24小时

# 性能配置
TRANSLATION_MAX_WORKERS=5  # 并行翻译线程数
TRANSLATION_BATCH_SIZE=100  # 批量处理大小
```

### 配置文件（可选）

```yaml
# config.yaml
translation:
  provider: google
  api_key: ${TRANSLATION_API_KEY}
  
  cache:
    type: file
    dir: .translation_cache
    ttl: 86400
    max_size: 10000
  
  performance:
    max_workers: 5
    batch_size: 100
  
  defaults:
    source_lang: auto
    target_lang: en
```

## 错误处理

```python
class TranslationError(Exception):
    """翻译错误基类"""
    pass


class APIError(TranslationError):
    """API调用错误"""
    pass


class LanguageNotSupportedError(TranslationError):
    """不支持的语言"""
    pass


class CacheError(TranslationError):
    """缓存错误"""
    pass
```

## 性能优化

1. **缓存策略**：
   - LRU缓存淘汰
   - 预加载常用翻译
   - 批量缓存操作

2. **并行处理**：
   - 批量翻译时并行调用API
   - 使用线程池或异步IO

3. **请求优化**：
   - 合并短文本
   - 批量API调用（如果支持）
   - 请求去重

4. **内存管理**：
   - 限制缓存大小
   - 定期清理过期缓存
   - 使用持久化缓存减少内存占用

## 扩展性

1. **多提供者支持**：可切换不同翻译服务
2. **自定义缓存后端**：支持Redis、数据库等
3. **插件系统**：支持自定义预处理/后处理
4. **监控和日志**：集成日志和性能监控

## 测试策略

1. **单元测试**：测试各个模块功能
2. **集成测试**：测试完整翻译流程
3. **性能测试**：测试缓存和批量处理性能
4. **错误处理测试**：测试各种异常情况
