import os
import sys

import pexpect
import pytest
from pexpect import spawn


@pytest.fixture
def pdbr_child_process(tmp_path) -> spawn:
    file = tmp_path / "foo.py"
    file.write_text("breakpoint()")
    env = os.environ.copy()
    env["IPY_TEST_SIMPLE_PROMPT"] = "1"
    child = pexpect.spawn(sys.executable, ["-m", "pdbr", str(file)], env=env)
    child.timeout = 3
    return child


def test_time(pdbr_child_process):
    pdbr_child_process.sendline("from time import sleep")
    pdbr_child_process.sendline("%time sleep(0.1)")
    pdbr_child_process.expect("CPU time")
    pdbr_child_process.expect("Wall time: 100 ms")


def test_timeit(pdbr_child_process):
    pdbr_child_process.sendline("%timeit -n 1 -r 1 pass")
    pdbr_child_process.expect_exact("std. dev. of 1 run, 1 loop each)")
