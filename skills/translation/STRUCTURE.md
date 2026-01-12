# 翻译 Skill 文件结构

## 完整目录树

```
translation/
│
├── SKILL.md                          # ⭐ Skill主文档（必需）
│   ├── YAML frontmatter
│   │   ├── name: translation
│   │   ├── description: 多语言翻译skill...
│   │   └── license: Complete terms in LICENSE.txt
│   └── 使用说明和指令
│
├── LICENSE.txt                       # 许可证文件（Apache 2.0）
│
├── requirements.txt                  # Python依赖（可选）
│   ├── googletrans==4.0.0rc1
│   ├── deepl
│   └── openai
│
├── README.md                         # 使用说明（可选）
│
├── PLAN.md                          # 📋 规划文档（本文档）
│
├── API_DESIGN.md                    # 📐 API设计文档
│
├── STRUCTURE.md                     # 📁 文件结构文档（本文件）
│
├── scripts/                         # 🐍 Python脚本目录
│   ├── __init__.py                  # 包初始化
│   │
│   ├── translator.py               # 核心翻译模块
│   │   ├── TranslationProvider (ABC)
│   │   ├── GoogleTranslateProvider
│   │   ├── DeepLProvider
│   │   ├── OpenAIProvider
│   │   └── Translator (主类)
│   │
│   ├── cache.py                    # 缓存管理模块
│   │   ├── TranslationCache (基类)
│   │   ├── MemoryCache
│   │   ├── FileCache
│   │   └── SQLiteCache
│   │
│   ├── batch_translator.py         # 批量翻译工具
│   │   ├── BatchTranslator
│   │   └── 并行处理逻辑
│   │
│   ├── utils.py                    # 工具函数
│   │   ├── normalize_language_code()
│   │   ├── get_language_name()
│   │   ├── preprocess_text()
│   │   └── chunk_texts()
│   │
│   └── exceptions.py               # 异常定义
│       ├── TranslationError
│       ├── APIError
│       ├── LanguageNotSupportedError
│       └── CacheError
│
├── examples/                        # 📚 示例目录
│   ├── basic_translation.md        # 基础翻译示例
│   ├── batch_translation.md        # 批量翻译示例
│   ├── cache_demo.md              # 缓存使用示例
│   └── multi_language.md          # 多语言示例
│
└── tests/                          # 🧪 测试目录（可选）
    ├── __init__.py
    ├── test_translator.py
    ├── test_cache.py
    └── test_batch.py
```

## 文件说明

### 核心文件

#### `SKILL.md` ⭐
- **必需文件**，Skill的核心
- 包含YAML frontmatter和详细使用说明
- 定义何时使用此skill以及如何使用

#### `LICENSE.txt`
- 许可证文件（Apache 2.0）
- 与其他skill保持一致

### 脚本模块

#### `scripts/translator.py`
**职责**：核心翻译功能
- `TranslationProvider`：抽象基类，定义翻译服务接口
- `GoogleTranslateProvider`：Google翻译实现
- `DeepLProvider`：DeepL翻译实现
- `OpenAIProvider`：OpenAI GPT翻译实现
- `Translator`：主翻译器类，整合缓存和提供者

**关键方法**：
- `translate()`：单文本翻译
- `translate_batch()`：批量翻译
- `detect_language()`：语言检测

#### `scripts/cache.py`
**职责**：缓存管理
- `TranslationCache`：缓存基类
- `MemoryCache`：内存缓存（快速但易失）
- `FileCache`：文件缓存（持久化）
- `SQLiteCache`：数据库缓存（大规模）

**关键方法**：
- `get()`：获取缓存
- `set()`：设置缓存
- `clear()`：清除缓存
- `stats()`：统计信息

#### `scripts/batch_translator.py`
**职责**：批量翻译优化
- 并行处理
- 批量API调用
- 智能分块
- 结果合并

#### `scripts/utils.py`
**职责**：工具函数
- 语言代码标准化
- 文本预处理
- 文本分块
- 其他辅助函数

#### `scripts/exceptions.py`
**职责**：异常定义
- 统一的错误处理
- 友好的错误消息

### 示例文件

#### `examples/basic_translation.md`
展示基础翻译用法：
```python
from scripts.translator import Translator, GoogleTranslateProvider

translator = Translator(GoogleTranslateProvider())
result = translator.translate("Hello", target_lang="zh")
```

#### `examples/batch_translation.md`
展示批量翻译用法：
```python
texts = ["Hello", "World", "Python"]
results = translator.translate_batch(texts, target_lang="zh")
```

#### `examples/cache_demo.md`
展示缓存功能：
```python
# 第一次翻译（调用API）
result1 = translator.translate("Hello", target_lang="zh")

# 第二次翻译（使用缓存）
result2 = translator.translate("Hello", target_lang="zh")
assert result2["cached"] == True
```

## 模块依赖关系

```
SKILL.md
    │
    └──► scripts/
            │
            ├──► translator.py
            │       ├──► cache.py
            │       ├──► utils.py
            │       └──► exceptions.py
            │
            ├──► batch_translator.py
            │       ├──► translator.py
            │       └──► cache.py
            │
            ├──► cache.py
            │       └──► utils.py
            │
            └──► utils.py
```

## 数据流

```
用户请求
    │
    ▼
SKILL.md (指令)
    │
    ▼
Translator.translate()
    │
    ├──► Cache.get() ──命中──► 返回
    │
    └──► Provider.translate()
            │
            └──► Cache.set()
                    │
                    └──► 返回
```

## 配置层次

```
1. 环境变量 (最高优先级)
   ├── TRANSLATION_API_KEY
   ├── TRANSLATION_PROVIDER
   └── TRANSLATION_CACHE_TYPE

2. 配置文件 (config.yaml)
   └── translation: {...}

3. 代码默认值 (最低优先级)
   └── Translator(provider, cache, defaults)
```

## 扩展建议

### 短期（MVP）
- ✅ 基础翻译功能
- ✅ 简单缓存（内存）
- ✅ 批量翻译（串行）

### 中期
- ⏳ 文件缓存持久化
- ⏳ 并行批量翻译
- ⏳ 多提供者支持

### 长期
- 🔮 SQLite/Redis缓存
- 🔮 翻译质量评估
- 🔮 自定义术语表
- 🔮 翻译记忆库（TM）

## 文件大小估算

```
SKILL.md:            ~5-10 KB
LICENSE.txt:         ~15 KB
requirements.txt:     ~0.5 KB
scripts/*.py:         ~50-100 KB (总计)
examples/*.md:        ~10-20 KB (总计)
README.md:           ~5 KB
─────────────────────────────
总计:                ~85-150 KB
```

## 下一步行动

1. ✅ 创建规划文档（已完成）
2. ⏳ 实现核心翻译模块
3. ⏳ 实现缓存模块
4. ⏳ 实现批量翻译
5. ⏳ 编写SKILL.md
6. ⏳ 创建示例文件
7. ⏳ 编写测试
8. ⏳ 文档完善
