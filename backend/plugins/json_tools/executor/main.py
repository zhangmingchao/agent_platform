"""JSON 进程插件：标准输入参数、标准输出结果，日志写 stderr。"""
import json
import sys


def main() -> None:
    """处理一次 JsonFormat 调用，返回结构化成功或失败结果。"""
    request = json.load(sys.stdin)
    args = request["arguments"]
    try:
        value = json.loads(args["content"])
        indent = args.get("indent", 2)
        formatted = json.dumps(value, ensure_ascii=False, indent=indent or None, separators=(",", ":") if indent == 0 else None,
                               sort_keys=args.get("sort_keys", False), allow_nan=False)
        result = {"ok": True, "data": {"formatted": formatted}, "error": None}
    except (ValueError, RecursionError):
        result = {"ok": False, "data": None, "error": {"code": "INVALID_JSON", "message": "JSON 文本无效"}}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
