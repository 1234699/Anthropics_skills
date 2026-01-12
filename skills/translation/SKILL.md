---
name: translation
description: 多语言翻译skill，支持多语言互译、批量翻译和智能缓存机制。当用户需要翻译文本、文档或进行多语言内容处理时使用此skill。
license: Complete terms in LICENSE.txt
---

# 翻译 Skill

一个功能强大的多语言翻译skill，支持多种翻译服务、批量处理和智能缓存。

## 功能特性

- **多语言互译**：支持任意两种语言之间的翻译，自动检测源语言
- **批量翻译**：高效处理大量文本，支持并行处理
- **智能缓存**：避免重复翻译，提高效率，支持内存、文件和数据库缓存
- **多服务支持**：支持Google Translate、DeepL、OpenAI等多种翻译服务

## 何时使用

在以下场景使用此skill：
- 翻译单个文本或短语
- 批量翻译多个文本片段
- 翻译文档或文件内容
- 多语言内容处理
- 语言检测和识别

## 快速开始

### 基础翻译

```python
from scripts.translator import Translator, GoogleTranslateProvider
from scripts.cache import MemoryCache

# 初始化翻译器
cache = MemoryCache()
provider = GoogleTranslateProvider()
translator = Translator(provider=provider, cache=cache)

# 翻译文本
result = translator.translate(
    "你好，世界！",
    source_lang="zh",
    target_lang="en"
)
print(result.text)  # "Hello, world!"
```

### 批量翻译

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
    print(f"{result.text}")
```

### 使用缓存

```python
from scripts.cache import FileCache

# 使用文件缓存（持久化）
cache = FileCache(cache_dir=".translation_cache")

translator = Translator(provider=provider, cache=cache)

# 第一次翻译（调用API）
result1 = translator.translate("Hello", target_lang="zh")

# 第二次翻译（使用缓存，更快）
result2 = translator.translate("Hello", target_lang="zh")
print(result2.cached)  # True
```

## 翻译服务配置

### Google Translate（推荐，免费）

```python
from scripts.translator import GoogleTranslateProvider

provider = GoogleTranslateProvider()
```

**安装依赖：**
```bash
pip install googletrans==4.0.0rc1
```

### DeepL（高质量翻译）

```python
from scripts.translator import DeepLProvider
import os

# 需要API密钥
provider = DeepLProvider(api_key=os.getenv("DEEPL_API_KEY"))
```

**安装依赖：**
```bash
pip install deepl
```

**环境变量：**
```bash
export DEEPL_API_KEY=your_api_key
```

### OpenAI GPT

```python
from scripts.translator import OpenAIProvider
import os

# 需要API密钥
provider = OpenAIProvider(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-3.5-turbo"
)
```

**安装依赖：**
```bash
pip install openai
```

**环境变量：**
```bash
export OPENAI_API_KEY=your_api_key
```

## 缓存配置

### 内存缓存（快速，易失）

```python
from scripts.cache import MemoryCache

cache = MemoryCache(max_size=10000, ttl=86400)
```

### 文件缓存（持久化）

```python
from scripts.cache import FileCache

cache = FileCache(
    cache_dir=".translation_cache",
    max_size=10000,
    ttl=86400  # 24小时
)
```

### SQLite缓存（大规模）

```python
from scripts.cache import SQLiteCache

cache = SQLiteCache(
    db_path=".translation_cache/cache.db",
    max_size=100000,
    ttl=86400
)
```

### 缓存管理

```python
# 查看缓存统计
stats = cache.stats()
print(f"命中率: {stats['hit_rate']:.2%}")
print(f"总条目: {stats['total_entries']}")

# 清除特定语言对的缓存
cache.clear(pattern="zh-en")

# 清除所有缓存
cache.clear()
```

## 高级用法

### 批量翻译工具

```python
from scripts.batch_translator import BatchTranslator

batch_translator = BatchTranslator(translator)

# 大批量翻译（自动分块）
results = batch_translator.translate_batch(
    texts,
    batch_size=100,
    max_workers=10
)

# 翻译文件（每行一个）
results = batch_translator.translate_file(
    "input.txt",
    source_lang="zh",
    target_lang="en"
)

# 翻译字典
data = {
    "title": "标题",
    "description": "描述",
    "items": ["项目1", "项目2"]
}
translated = batch_translator.translate_dict(
    data,
    source_lang="zh",
    target_lang="en"
)
```

### 语言检测

```python
# 检测文本语言
detection = translator.detect_language("Hello, world!")
print(detection["language"])  # "en"
print(detection["confidence"])  # 0.98
```

### 自动语言检测

```python
# 使用auto自动检测源语言
result = translator.translate(
    "Bonjour le monde",
    source_lang="auto",  # 自动检测
    target_lang="en"
)
print(result.source_lang)  # "fr" (检测到的语言)
```

## 错误处理

```python
from scripts.exceptions import (
    TranslationError,
    APIError,
    LanguageNotSupportedError,
    CacheError,
)

try:
    result = translator.translate("Hello", target_lang="invalid")
except LanguageNotSupportedError as e:
    print(f"不支持的语言: {e.language}")
except APIError as e:
    print(f"API错误: {e.message}")
except TranslationError as e:
    print(f"翻译错误: {e}")
```

## 性能优化

### 并行处理

批量翻译时启用并行处理可以显著提高速度：

```python
results = translator.translate_batch(
    texts,
    parallel=True,  # 启用并行
    use_cache=True  # 使用缓存
)
```

### 缓存策略

- **内存缓存**：适合短期、高频翻译
- **文件缓存**：适合需要持久化的场景
- **SQLite缓存**：适合大规模、长期使用

### 批量处理

对于大量文本，使用批量翻译工具自动分块：

```python
batch_translator = BatchTranslator(translator)
results = batch_translator.translate_batch(
    large_text_list,
    batch_size=100,  # 每批100条
    max_workers=5    # 5个并行线程
)
```

## 工具函数

```python
from scripts.utils import (
    normalize_language_code,
    get_language_name,
    preprocess_text,
    validate_language_code,
    get_supported_languages,
)

# 标准化语言代码
code = normalize_language_code("zh-CN")  # "zh"

# 获取语言名称
name = get_language_name("zh")  # "Chinese"

# 预处理文本
text = preprocess_text("  Hello   World  ")  # "Hello World"

# 验证语言代码
is_valid = validate_language_code("en")  # True

# 获取支持的语言列表
languages = get_supported_languages()
```

## 最佳实践

1. **选择合适的翻译服务**
   - Google Translate：免费，支持语言多
   - DeepL：质量高，适合正式文档
   - OpenAI：灵活，可定制提示词

2. **使用缓存**
   - 对于重复翻译，缓存可以显著提高速度
   - 选择合适的缓存类型（内存/文件/数据库）

3. **批量处理**
   - 对于大量文本，使用批量翻译而不是循环调用
   - 启用并行处理提高效率

4. **错误处理**
   - 始终处理可能的异常
   - 提供友好的错误消息

5. **语言代码**
   - 使用ISO 639-1标准语言代码
   - 使用`normalize_language_code`标准化代码

## 示例场景

### 场景1：翻译用户输入

```python
user_input = "How are you?"
result = translator.translate(user_input, target_lang="zh")
print(result.text)  # "你好吗？"
```

### 场景2：批量翻译产品描述

```python
descriptions = [
    "High quality product",
    "Fast shipping",
    "Customer satisfaction guaranteed"
]

results = translator.translate_batch(
    descriptions,
    target_lang="zh",
    parallel=True
)

for i, result in enumerate(results):
    print(f"{i+1}. {result.text}")
```

### 场景3：多语言网站内容

```python
content = {
    "title": "Welcome",
    "subtitle": "To our website",
    "menu": {
        "home": "Home",
        "about": "About",
        "contact": "Contact"
    }
}

batch_translator = BatchTranslator(translator)
translated_content = batch_translator.translate_dict(
    content,
    target_lang="zh"
)
```

## 注意事项

1. **API限制**：不同翻译服务有不同的速率限制，注意控制请求频率
2. **成本**：某些服务（如DeepL、OpenAI）需要付费API密钥
3. **准确性**：自动翻译可能不完美，重要内容建议人工审核
4. **隐私**：翻译内容可能发送到第三方服务，注意数据隐私

## 依赖安装

根据使用的翻译服务安装相应依赖：

```bash
# Google Translate
pip install googletrans==4.0.0rc1

# DeepL
pip install deepl

# OpenAI
pip install openai
```

或安装所有依赖：

```bash
pip install -r requirements.txt
```

## 更多信息

- 查看 `PLAN.md` 了解详细规划
- 查看 `API_DESIGN.md` 了解API设计
- 查看 `STRUCTURE.md` 了解文件结构
- 查看 `examples/` 目录获取更多示例
