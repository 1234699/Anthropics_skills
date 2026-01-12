# 基础翻译示例

## 示例1：简单翻译

```python
from scripts.translator import Translator, GoogleTranslateProvider
from scripts.cache import MemoryCache

# 初始化
cache = MemoryCache()
provider = GoogleTranslateProvider()
translator = Translator(provider=provider, cache=cache)

# 翻译
result = translator.translate(
    "Hello, world!",
    source_lang="en",
    target_lang="zh"
)

print(result.text)  # "你好，世界！"
print(result.source_lang)  # "en"
print(result.target_lang)  # "zh"
print(result.cached)  # False (第一次翻译)
```

## 示例2：自动检测源语言

```python
# 使用auto自动检测源语言
result = translator.translate(
    "Bonjour le monde",
    source_lang="auto",  # 自动检测
    target_lang="en"
)

print(result.text)  # "Hello world"
print(result.source_lang)  # "fr" (检测到的语言)
```

## 示例3：语言检测

```python
# 检测文本语言
detection = translator.detect_language("Hola, mundo!")
print(detection["language"])  # "es"
print(detection.get("confidence"))  # 可能的值，取决于提供者
```

## 示例4：使用不同翻译服务

### Google Translate（免费）

```python
from scripts.translator import GoogleTranslateProvider

provider = GoogleTranslateProvider()
translator = Translator(provider=provider)
result = translator.translate("Hello", target_lang="zh")
```

### DeepL（高质量）

```python
from scripts.translator import DeepLProvider
import os

provider = DeepLProvider(api_key=os.getenv("DEEPL_API_KEY"))
translator = Translator(provider=provider)
result = translator.translate("Hello", target_lang="zh")
```

### OpenAI GPT

```python
from scripts.translator import OpenAIProvider
import os

provider = OpenAIProvider(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-3.5-turbo"
)
translator = Translator(provider=provider)
result = translator.translate("Hello", target_lang="zh")
```
