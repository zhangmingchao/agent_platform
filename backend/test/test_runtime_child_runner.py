"""本地 Python Runtime 子进程入口测试。"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class RuntimeChildRunnerTests(unittest.TestCase):
    """验证结构化结果写出和工作目录访问限制。"""

    def _run_code(self, code: str) -> tuple[subprocess.CompletedProcess, Path, tempfile.TemporaryDirectory]:
        """在临时工作目录中运行子进程入口并返回运行结果。"""
        temporary = tempfile.TemporaryDirectory()
        workspace = Path(temporary.name)
        source_dir = workspace / "source"
        input_dir = workspace / "input"
        output_dir = workspace / "output"
        for directory in (source_dir, input_dir, output_dir):
            directory.mkdir()
        source_path = source_dir / "main.py"
        source_path.write_text(code, encoding="utf-8")
        config_path = workspace / "runtime.json"
        config_path.write_text(json.dumps({
            "workspace": str(workspace),
            "sourcePath": str(source_path),
            "inputDir": str(input_dir),
            "outputDir": str(output_dir),
            "inputFiles": {},
            "arguments": {},
        }), encoding="utf-8")
        runner = Path(__file__).resolve().parents[1] / "runtime" / "child_runner.py"
        process = subprocess.run(
            [sys.executable, "-I", str(runner), str(config_path)],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return process, output_dir, temporary

    def test_writes_result_and_artifact(self) -> None:
        """允许向 output 目录写文件，并自动保存 result。"""
        process, output_dir, temporary = self._run_code(
            "from pathlib import Path\n"
            "Path(OUTPUT_DIR, 'answer.txt').write_text('ok', encoding='utf-8')\n"
            "result = {'ok': True}\n"
        )
        try:
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(json.loads((output_dir / "result.json").read_text()), {"ok": True})
            self.assertEqual((output_dir / "answer.txt").read_text(), "ok")
        finally:
            temporary.cleanup()

    def test_imports_openpyxl_with_system_mime_data(self) -> None:
        """允许 openpyxl 读取标准库声明的系统 MIME 类型文件。"""
        process, output_dir, temporary = self._run_code(
            "import openpyxl\nresult = {'version': openpyxl.__version__}\n"
        )
        try:
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn("version", json.loads((output_dir / "result.json").read_text()))
        finally:
            temporary.cleanup()

    def test_denies_reading_outside_workspace(self) -> None:
        """拒绝读取工作目录和 Python 安装目录之外的文件。"""
        process, _, temporary = self._run_code("open('/etc/hosts').read()\n")
        try:
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("Runtime 不允许读取", process.stderr)
        finally:
            temporary.cleanup()

    def test_denies_deleting_outside_output(self) -> None:
        """即使使用 pathlib，也不允许删除 output 目录之外的文件。"""
        process, _, temporary = self._run_code(
            "from pathlib import Path\nPath(INPUT_DIR, 'missing.txt').unlink(missing_ok=True)\n"
        )
        try:
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("Runtime 仅允许修改", process.stderr)
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
