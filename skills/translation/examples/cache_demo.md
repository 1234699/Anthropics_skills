# 缓存使用示例

## 示例1：内存缓存

```python
from scripts.cache import MemoryCache
from scripts.translator import Translator, GoogleTranslateProvider

# 使用内存缓存（快速但易失）
cache = MemoryCache(max_size=10000, ttl=86400)  # 24小时过期
translator = Translator(
    provider=GoogleTranslateProvider(),
    cache=cache
)

# 第一次翻译（调用API）
result1 = translator.translate("Hello", target_lang="zh")
print(result1.cached)  # False

# 第二次翻译（使用缓存）
result2 = translator.translate("Hello", target_lang="zh")
print(result2.cached)  # True
print(result2.text == result1.text)  # True
```

## 示例2：文件缓存（持久化）

```python
from scripts.cache import FileCache

# 使用文件缓存（持久化，重启后仍然有效）
cache = FileCache(
    cache_dir=".translation_cache",
    max_size=10000,
    ttl=86400  # 24小时
)

translator = Translator(
    provider=GoogleTranslateProvider(),
    cache=cache
)

# 翻译并保存到文件缓存
result = translator.translate("Hello", target_lang="zh")

# 即使重启程序，缓存仍然有效
```

## 示例3：SQLite缓存（大规模）

```python
from scripts.cache import SQLiteCache

# 使用SQLite缓存（适合大规模使用）
cache = SQLiteCache(
    db_path=".translation_cache/cache.db",
    max_size=100000,  # 支持更多条目
    ttl=86400
)

translator = Translator(
    provider=GoogleTranslateProvider(),
    cache=cache
)
```

## 示例4：查看缓存统计

```python
# 执行一些翻译
translator.translate("Hello", target_lang="zh")
translator.translate("World", target_lang="zh")
translator.translate("Hello", target_lang="zh")  # 缓存命中

# 查看统计信息
stats = cache.stats()
print(f"总条目: {stats['total_entries']}")
print(f"命中次数: {stats['hits']}")
print(f"未命中次数: {stats['misses']}")
print(f"命中率: {stats['hit_rate']:.2%}")
print(f"缓存大小: {stats['size_mb']:.2f} MB")
print(f"缓存类型: {stats['type']}")
```

## 示例5：清除缓存

```python
# 清除特定语言对的缓存
count = cache.clear(pattern="zh-en")
print(f"清除了 {count} 条缓存")

# 清除所有缓存
count = cache.clear()
print(f"清除了所有 {count} 条缓存")
```

## 示例6：禁用缓存

```python
# 某些情况下可能需要禁用缓存
result = translator.translate(
    "Hello",
    target_lang="zh",
    use_cache=False  # 禁用缓存
)
```

## 示例7：缓存预热

```python
# 预先翻译常用文本，填充缓存
common_texts = [
    "Hello",
    "Thank you",
    "Please",
    "Yes",
    "No"
]

# 批量翻译并填充缓存
translator.translate_batch(
    common_texts,
    target_lang="zh",
    use_cache=True  # 保存到缓存
)

# 后续使用这些翻译时，会直接从缓存读取
```

## 示例8：缓存性能对比

```python
import time

texts = ["Hello"] * 100

# 不使用缓存
start = time.time()
for text in texts:
    translator.translate(text, target_lang="zh", use_cache=False)
no_cache_time = time.time() - start

# 使用缓存（第二次运行）
start = time.time()
for text in texts:
    translator.translate(text, target_lang="zh", use_cache=True)
cache_time = time.time() - start

print(f"无缓存: {no_cache_time:.2f}秒")
print(f"有缓存: {cache_time:.2f}秒")
print(f"加速比: {no_cache_time/cache_time:.1f}x")
```
