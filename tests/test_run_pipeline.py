from __future__ import annotations

import unittest
from unittest.mock import call, patch

from scripts import run_pipeline


class PipelineModeTests(unittest.TestCase):
    @patch("scripts.run_pipeline.run_step")
    def test_default_pipeline_is_offline(self, run_step) -> None:
        self.assertEqual(run_pipeline.main([]), 0)
        self.assertEqual(
            run_step.call_args_list,
            [call("analyze.py"), call("build_reports.py"), call("verify_project.py")],
        )

    @patch("scripts.run_pipeline.run_step")
    def test_refresh_pipeline_passes_explicit_fetch_guard(self, run_step) -> None:
        self.assertEqual(run_pipeline.main(["--refresh-data"]), 0)
        self.assertEqual(
            run_step.call_args_list,
            [
                call("fetch_data.py", "--refresh-data"),
                call("analyze.py"),
                call("build_reports.py"),
                call("verify_project.py"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
