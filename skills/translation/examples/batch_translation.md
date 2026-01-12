# 批量翻译示例

## 示例1：基础批量翻译

```python
from scripts.translator import Translator, GoogleTranslateProvider
from scripts.cache import MemoryCache

translator = Translator(
    provider=GoogleTranslateProvider(),
    cache=MemoryCache()
)

# 批量翻译
texts = [
    "Hello",
    "World",
    "Python",
    "Translation"
]

results = translator.translate_batch(
    texts,
    source_lang="en",
    target_lang="zh",
    parallel=True  # 并行处理
)

for result in results:
    print(f"{result.text}")
```

## 示例2：使用批量翻译工具

```python
from scripts.batch_translator import BatchTranslator

batch_translator = BatchTranslator(translator)

# 大批量翻译（自动分块）
large_text_list = ["Text " + str(i) for i in range(1000)]

results = batch_translator.translate_batch(
    large_text_list,
    source_lang="en",
    target_lang="zh",
    batch_size=100,  # 每批100条
    max_workers=5    # 5个并行线程
)

print(f"翻译了 {len(results)} 条文本")
```

## 示例3：翻译文件

```python
# 假设有一个文件 input.txt，每行一个文本
# Hello
# World
# Python

results = batch_translator.translate_file(
    "input.txt",
    source_lang="en",
    target_lang="zh"
)

# 保存结果
with open("output.txt", "w", encoding="utf-8") as f:
    for result in results:
        f.write(result.text + "\n")
```

## 示例4：翻译字典

```python
# 翻译嵌套字典结构
data = {
    "title": "Welcome",
    "subtitle": "To our website",
    "menu": {
        "home": "Home",
        "about": "About Us",
        "contact": "Contact"
    },
    "items": [
        "Item 1",
        "Item 2",
        "Item 3"
    ]
}

translated = batch_translator.translate_dict(
    data,
    source_lang="en",
    target_lang="zh"
)

print(translated)
# {
#     "title": "欢迎",
#     "subtitle": "访问我们的网站",
#     "menu": {
#         "home": "首页",
#         "about": "关于我们",
#         "contact": "联系方式"
#     },
#     "items": ["项目1", "项目2", "项目3"]
# }
```

## 示例5：处理翻译结果

```python
results = translator.translate_batch(
    texts,
    source_lang="en",
    target_lang="zh"
)

# 检查哪些来自缓存
cached_count = sum(1 for r in results if r.cached)
print(f"缓存命中: {cached_count}/{len(results)}")

# 提取翻译文本
translated_texts = [r.text for r in results]

# 检查翻译质量（如果有置信度）
for result in results:
    if result.confidence:
        print(f"{result.text}: {result.confidence:.2%}")
```
