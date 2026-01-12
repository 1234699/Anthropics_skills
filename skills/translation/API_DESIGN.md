# 翻译 Skill API 设计文档

## 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    SKILL.md (指令层)                     │
│              定义何时以及如何使用翻译功能                 │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Translator (主翻译器类)                      │
│  ┌──────────────┐         ┌──────────────┐              │
│  │   Provider   │         │    Cache    │              │
│  │  (翻译服务)   │◄───────►│  (缓存管理)  │              │
│  └──────────────┘         └──────────────┘              │
└─────────────────────────────────────────────────────────┘
         │                          │
         ▼                          ▼
┌─────────────────┐      ┌──────────────────────┐
│ Google Translate│      │ Memory Cache         │
│ DeepL           │      │ File Cache           │
│ OpenAI          │      │ SQLite Cache         │
└─────────────────┘      └──────────────────────┘
```

## 核心API接口

### 1. 翻译接口

#### `translate()` - 单文本翻译

**签名：**
```python
translate(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "en",
    use_cache: bool = True,
    **options
) -> TranslationResult
```

**流程：**
```
输入文本
    │
    ▼
检查缓存 ──命中──► 返回缓存结果
    │
   未命中
    │
    ▼
调用翻译服务
    │
    ▼
保存到缓存
    │
    ▼
返回翻译结果
```

**返回类型：**
```python
@dataclass
class TranslationResult:
    text: str                    # 翻译后的文本
    source_lang: str            # 源语言代码
    target_lang: str            # 目标语言代码
    confidence: float | None    # 置信度（0-1）
    cached: bool                # 是否来自缓存
    provider: str               # 使用的翻译服务
    metadata: dict              # 其他元数据
```

#### `translate_batch()` - 批量翻译

**签名：**
```python
translate_batch(
    texts: list[str],
    source_lang: str = "auto",
    target_lang: str = "en",
    use_cache: bool = True,
    parallel: bool = True,
    batch_size: int = 100,
    **options
) -> list[TranslationResult]
```

**流程：**
```
输入文本列表
    │
    ▼
批量检查缓存 ──部分命中──► 分离已缓存和未缓存
    │
    ▼
并行翻译未缓存文本 ──► 批量保存到缓存
    │
    ▼
合并结果（保持顺序）
    │
    ▼
返回结果列表
```

**优化策略：**
- 并行处理：使用线程池或异步IO
- 批量API调用：如果服务支持，合并请求
- 智能分块：根据文本长度动态调整批次大小

### 2. 缓存接口

#### 缓存键生成策略

```python
cache_key = hash(
    text_normalized + 
    source_lang + 
    target_lang + 
    options_hash
)
```

**考虑因素：**
- 文本规范化（去除多余空格、统一编码）
- 语言代码标准化（zh-CN → zh）
- 选项影响（某些选项会影响翻译结果）

#### 缓存层级

```
L1: 内存缓存（快速访问）
    │
    ▼
L2: 文件缓存（持久化）
    │
    ▼
L3: 数据库缓存（大规模）
```

#### 缓存策略

- **写入策略**：Write-through（同步写入）
- **淘汰策略**：LRU（最近最少使用）
- **过期策略**：TTL（生存时间）
- **预加载**：常用翻译对预加载

### 3. 语言检测接口

```python
detect_language(text: str) -> LanguageDetectionResult

@dataclass
class LanguageDetectionResult:
    language: str              # 检测到的语言代码
    confidence: float          # 置信度（0-1）
    alternatives: list[dict]   # 备选语言及置信度
```

## 数据流图

### 单文本翻译流程

```
User Request
    │
    ▼
┌─────────────────┐
│  Preprocessing  │  (文本清理、规范化)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Cache Lookup   │  (生成缓存键，查询缓存)
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
  命中      未命中
    │         │
    │         ▼
    │    ┌──────────────┐
    │    │ API Call     │  (调用翻译服务)
    │    └──────┬───────┘
    │           │
    │           ▼
    │    ┌──────────────┐
    │    │ Cache Store  │  (保存到缓存)
    │    └──────┬───────┘
    │           │
    └───────────┘
         │
         ▼
┌─────────────────┐
│ Postprocessing  │  (结果格式化、验证)
└────────┬────────┘
         │
         ▼
    Response
```

### 批量翻译流程

```
Text List Input
    │
    ▼
┌──────────────────┐
│ Batch Cache      │  (并行查询所有缓存)
│ Lookup           │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
  全部命中   部分/全部未命中
    │         │
    │         ▼
    │    ┌──────────────┐
    │    │ Chunk Texts │  (分块处理)
    │    └──────┬───────┘
    │           │
    │           ▼
    │    ┌──────────────┐
    │    │ Parallel     │  (并行翻译)
    │    │ Translation  │
    │    └──────┬───────┘
    │           │
    │           ▼
    │    ┌──────────────┐
    │    │ Batch Cache  │  (批量保存)
    │    │ Store        │
    │    └──────┬───────┘
    │           │
    └───────────┘
         │
         ▼
┌──────────────────┐
│ Merge Results    │  (合并结果，保持顺序)
└────────┬─────────┘
         │
         ▼
    Response List
```

## 错误处理流程

```
API Call
    │
    ▼
┌──────────────┐
│ Try Request │
└──────┬───────┘
       │
   ┌───┴───┐
   │       │
 成功     失败
   │       │
   │       ▼
   │   ┌──────────────┐
   │   │ Retry Logic  │  (指数退避重试)
   │   └──────┬───────┘
   │          │
   │     ┌────┴────┐
   │     │         │
   │   成功      失败
   │     │         │
   │     │         ▼
   │     │    ┌──────────────┐
   │     │    │ Fallback     │  (备用服务)
   │     │    │ Provider     │
   │     │    └──────┬───────┘
   │     │           │
   └─────┴───────────┘
            │
            ▼
       Return Result
            │
            ▼
    ┌───────────────┐
    │ Error Handler │  (记录错误、返回友好消息)
    └───────────────┘
```

## 性能指标

### 缓存性能

- **命中率目标**：> 80%（重复翻译场景）
- **缓存查询时间**：< 1ms（内存），< 10ms（文件）
- **缓存写入时间**：< 5ms（异步写入）

### 翻译性能

- **单文本翻译**：< 500ms（无缓存）
- **批量翻译（100条）**：< 5s（并行）
- **吞吐量**：> 1000条/分钟

### 资源使用

- **内存占用**：< 100MB（默认配置）
- **磁盘占用**：可配置（文件缓存）
- **并发连接**：可配置（API限制）

## 配置示例

### 最小配置

```python
from scripts.translator import Translator, GoogleTranslateProvider
from scripts.cache import TranslationCache

cache = TranslationCache(cache_type="memory")
provider = GoogleTranslateProvider()
translator = Translator(provider=provider, cache=cache)

result = translator.translate("Hello", target_lang="zh")
```

### 完整配置

```python
from scripts.translator import Translator, DeepLProvider
from scripts.cache import TranslationCache

cache = TranslationCache(
    cache_type="file",
    cache_dir=".translation_cache",
    max_size=50000,
    ttl=7 * 24 * 3600  # 7天
)

provider = DeepLProvider(
    api_key=os.getenv("DEEPL_API_KEY"),
    formality="default"
)

translator = Translator(
    provider=provider,
    cache=cache,
    default_source_lang="auto",
    default_target_lang="en"
)

# 批量翻译配置
results = translator.translate_batch(
    texts,
    source_lang="zh",
    target_lang="en",
    parallel=True,
    batch_size=50,
    max_workers=10
)
```

## 扩展点

### 1. 自定义提供者

```python
class CustomProvider(TranslationProvider):
    def translate(self, text, source_lang, target_lang, **options):
        # 实现自定义翻译逻辑
        pass
```

### 2. 自定义缓存后端

```python
class RedisCache(TranslationCache):
    def __init__(self, redis_client):
        # 使用Redis作为缓存后端
        pass
```

### 3. 文本预处理插件

```python
def custom_preprocessor(text: str) -> str:
    # 自定义文本预处理
    return text

translator.add_preprocessor(custom_preprocessor)
```

### 4. 结果后处理插件

```python
def custom_postprocessor(result: TranslationResult) -> TranslationResult:
    # 自定义结果处理
    return result

translator.add_postprocessor(custom_postprocessor)
```
