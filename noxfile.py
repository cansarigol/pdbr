import nox

nox.options.stop_on_first_error = True

SOURCE_FILES = "pdbr", "tests", "noxfile.py"


@nox.session
def lint(session, reuse_venv=True):
    session.install("autoflake", "isort==5.*", "black>=20.8b1")
    session.run("autoflake", "--in-place", "--recursive", *SOURCE_FILES)
    session.run("black", *SOURCE_FILES)
    session.run("isort", *SOURCE_FILES)


@nox.session
def check(session, reuse_venv=True):
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files")


@nox.session(python=["3.6.13", "3.7", "3.8", "3.9"])
def test(session, reuse_venv=True):
    session.install("pytest", "pytest-cov", "rich", "icecream", "prompt_toolkit")
    session.run("pytest", "--cov-report", "term-missing", "--cov=pdbr", "tests")


@nox.session
@nox.parametrize("django", ["1.8", "1.11", "2.0", "2.2", "3.0"])
def django_test(session, django, reuse_venv=True):
    session.install(f"django=={django}", "rich", "pytest")
    session.run("python", "runtests.py")
