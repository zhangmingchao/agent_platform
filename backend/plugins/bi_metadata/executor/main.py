"""BI 进程插件：平台配置通过环境 JSON 注入，复用包内只读 CLI。"""
import asyncio
import json
import os
import sys
from pathlib import Path


def main() -> None:
    """处理一次声明工具调用；保留 BiCli，新增目录、BI/Rule 查询和修改入口。"""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from bi_cli.commands import parse_bi_cli_command
    from bi_cli.models import BiCliSettings
    from bi_cli.client import BiApiClient
    request = json.load(sys.stdin)
    values = json.loads(os.environ.get("PLUGIN_VALUES", "{}"))
    secrets = json.loads(os.environ.get("PLUGIN_SECRETS", "{}"))
    if request.get("tool_name", "BiCli") != "BiCli":
        from solar_api.client import ApiFailure, ApiResult, dispatch
        try:
            response = asyncio.run(dispatch(request["tool_name"], request["arguments"], values, secrets))
            output = response.to_json(tuple(secrets.values()))
            # 输出上限同时覆盖目录详情，避免大型契约淹没模型上下文或被监督器截断。
            if len(output.encode()) > min(int(values.get("max_output_bytes", 1048576)), 950_000):
                output = ApiResult(False, error=ApiFailure("OUTPUT_TOO_LARGE", "契约或结果过大，请读取单个参考文件或缩小查询范围")).to_json()
        except Exception:
            output = ApiResult(False, error=ApiFailure("EXECUTION_ERROR", "接口插件执行异常，请检查配置和插件版本")).to_json()
        print(output)
        return
    try:
        # 配置验证和业务调用都返回标准失败结果，避免配置异常只留下进程堆栈。
        settings = BiCliSettings(base_url=values["base_url"], access_token=secrets["token"],
                                 timeout_seconds=int(values.get("timeout_seconds", 30)),
                                 max_output_bytes=int(values.get("max_output_bytes", 1048576)))
        command = parse_bi_cli_command(request["arguments"]["arguments"])
        response = asyncio.run(BiApiClient(settings).execute(command))
        result = {"ok": True, "data": response.to_mapping(), "error": None} if response.ok else {"ok": False, "data": None, "error": {"code": response.error_code or "BI_QUERY_FAILED", "message": response.message}}
    except Exception:
        result = {"ok": False, "data": None, "error": {"code": "BI_QUERY_FAILED", "message": "BI 查询失败，请检查配置与参数"}}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
