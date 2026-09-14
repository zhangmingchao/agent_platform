import asyncio
import dataclasses
import json
import typing



@dataclasses.dataclass
class ResultState:
    name:str
    age:int
    data:dict[str,typing.Any]



StateRunner = typing.Callable[
    [typing.Dict[str,typing.Any],ResultState],
    typing.Awaitable[str],
]




async def get_weather(data:dict[str,typing.Any],state:ResultState) -> str:
    state.data["weather"] = "天气晴朗"
    return "天气晴朗";




async def get_dbUrl(data:dict[str,typing.Any],state:ResultState) -> str:
    state.data["dbUrl"] = "www.baidu.com"
    return "www.baidu.com";




async def execute(runner:StateRunner,data:dict[str,typing.Any],state:ResultState) -> None:
    result_data = await runner(data,state)
    print(result_data)
    print(
        json.dumps(
            dataclasses.asdict(state),
            ensure_ascii=False,
            indent=2,
        )
    )

async def main() -> None:
    state = ResultState(name="zhangsan",age=13,data={"prompt":"查询天气与db的url"})
    await execute(get_weather,{"prompt":"查询天气与db的url"},state)
    await execute(get_dbUrl, state.data, state)


if __name__ == "__main__":
    asyncio.run(main())