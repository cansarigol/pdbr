import nox

nox.options.stop_on_first_error = True


@nox.session
def test(session, reuse_venv=True):
    session.install(
        ".",
        "pytest",
        "pytest-cov",
        "rich",
        "icecream",
        "prompt_toolkit",
        "sqlparse",
        "IPython",
    )
    session.run(
        "pytest",
        "--cov-report",
        "term-missing",
        "--cov=pdbr",
        "--capture=no",
        "--disable-warnings",
        "tests",
    )


@nox.session
@nox.parametrize("django", ["2.2", "3.2", "4.2"])
def django_test(session, django, reuse_venv=True):
    session.install(f"django=={django}", "rich", "pytest", "sqlparse")
    session.run("python", "runtests.py")
