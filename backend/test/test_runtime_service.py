"""Python Runtime 服务辅助逻辑测试。"""

import unittest
from backend.runtime.models import RuntimeContext
from backend.services.runtime_service import _rewrite_virtual_input_paths, _workspace_id


class RuntimeServiceTests(unittest.TestCase):
    """验证 Runtime 服务的虚拟文件路径兼容逻辑。"""

    def test_rewrites_known_mnt_data_path(self):
        """将已上传文件的 /mnt/data 路径改写为执行工作区路径。"""
        code = "file_path = '/mnt/data/report.xlsx'\nprint(file_path)"
        rewritten = _rewrite_virtual_input_paths(
            code,
            {"report.xlsx": "/runtime/input/123_report.xlsx"},
        )
        self.assertIn("/runtime/input/123_report.xlsx", rewritten)
        self.assertNotIn("/mnt/data/report.xlsx", rewritten)

    def test_keeps_unknown_mnt_data_path(self):
        """未上传的文件路径不应被猜测或替换。"""
        code = "file_path = '/mnt/data/unknown.xlsx'"
        rewritten = _rewrite_virtual_input_paths(code, {"report.xlsx": "/runtime/input/report.xlsx"})
        self.assertIn("/mnt/data/unknown.xlsx", rewritten)

    def test_workspace_is_scoped_inside_single_user_container(self):
        """显式 workspace_id 只作为安全目录名使用。"""
        context = RuntimeContext(user_id=7, workspace_id="project-2026")
        self.assertEqual(_workspace_id(context), "project-2026")

    def test_workspace_defaults_to_session(self):
        """聊天未显式传 workspace 时稳定映射到会话工作空间。"""
        context = RuntimeContext(user_id=7, session_id=88)
        self.assertEqual(_workspace_id(context), "session-88")

if __name__ == "__main__":
    unittest.main()
