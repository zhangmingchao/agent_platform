"""允许通过 `python -m backend.bi_cli` 执行 BI CLI。"""

from .main import main


if __name__ == "__main__":
    raise SystemExit(main())
