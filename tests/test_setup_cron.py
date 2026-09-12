from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SetupCronTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        temp = Path(self.temp_dir.name)
        self.project = temp / "owner's repo"
        self.mock_bin = temp / "mock bin"
        self.python_bin = temp / "py 'bin'" / "python3"
        self.state = temp / "crontab.state"
        (self.project / "scripts").mkdir(parents=True)
        self.mock_bin.mkdir()
        self.python_bin.parent.mkdir()
        shutil.copy2(ROOT / "main.py", self.project / "main.py")
        shutil.copy2(ROOT / "scripts" / "setup_cron.sh", self.project / "scripts" / "setup_cron.sh")
        shutil.copy2(sys.executable, self.python_bin)
        crontab = self.mock_bin / "crontab"
        crontab.write_text(
            """#!/usr/bin/env bash
if [ "$1" = "-l" ]; then
  if [ "${CRONTAB_MODE:-}" = denied ]; then echo "permission denied" >&2; exit 1; fi
  if [ -f "$CRONTAB_STATE" ]; then cat "$CRONTAB_STATE"; else echo "no crontab for test" >&2; exit 1; fi
elif [ "$1" = "-" ]; then
  cat > "$CRONTAB_STATE"
else
  exit 2
fi
""",
            encoding="utf-8",
        )
        crontab.chmod(0o755)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_setup(self, *, mode: str = "") -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "CRONTAB_MODE": mode,
                "CRONTAB_STATE": str(self.state),
                "PATH": f"{self.mock_bin}:{env['PATH']}",
                "PYTHON_BIN": str(self.python_bin),
            }
        )
        return subprocess.run(
            ["bash", str(self.project / "scripts" / "setup_cron.sh")],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_preserves_unrelated_cron_and_is_idempotent_for_quoted_paths(self) -> None:
        self.state.write_text("# keep this line\n17 4 * * * /bin/true\n", encoding="utf-8")

        first = self.run_setup()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        content = self.state.read_text(encoding="utf-8")
        self.assertEqual(content.count("# keep this line"), 1)
        self.assertEqual(content.count("17 4 * * * /bin/true"), 1)
        self.assertEqual(content.count("0 6 * * * cd '"), 1)
        self.assertIn("owner'\\''s repo", content)
        self.assertIn("py '\\''bin", content)

        second = self.run_setup()
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(self.state.read_text(encoding="utf-8"), content)

        denied = self.run_setup(mode="denied")
        self.assertNotEqual(denied.returncode, 0)
        self.assertEqual(self.state.read_text(encoding="utf-8"), content)


if __name__ == "__main__":
    unittest.main()
