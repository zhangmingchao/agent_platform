# Python 方法返回值类型规范

## 规范

项目自有 Python 函数、异步函数、类方法和内部函数必须声明返回值类型：

```python
def normalize_name(name: str) -> str:
    return name.strip()


async def save_result(result: RuntimeResult) -> None:
    await repository.save(result)
```

- 无返回值的方法使用 `-> None`。
- 异步方法标注 `await` 后得到的实际结果类型，不标注为 `Coroutine`。
- 异步生成器使用 `AsyncIterator[T]` 或 `AsyncGenerator[T, None]`。
- 工厂方法使用实际实体、协议或抽象基类，不使用无含义的 `object`。
- LangGraph 编译结果使用 `CompiledStateGraph`。
- 动态工具函数使用 `Callable[..., Awaitable[T]]`。

## 扫描边界

自动规范测试覆盖：

- `backend` 正式业务源码；
- Demo 与迁移脚本；
- 后端测试代码。

不扫描：

- `.venv`、`.venv-langchan` 第三方依赖；
- `backend/data/runtime` 中大模型生成的用户执行代码；
- Python 缓存目录。

## 自动守卫

`backend/test/test_type_annotations.py` 使用 Python AST 检查所有项目方法。新增方法没有返回值标注时，测试会输出对应文件、行号和方法名。
