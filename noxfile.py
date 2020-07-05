import nox

nox.options.stop_on_first_error = True

SOURCE_FILES = "pdbr", "tests", "noxfile.py"


@nox.session
def lint(session, reuse_venv=True):
    session.install("autoflake", "isort==5.*", "black")
    session.run("autoflake", "--in-place", "--recursive", *SOURCE_FILES)
    session.run("black", *SOURCE_FILES)
    session.run("isort", *SOURCE_FILES)


@nox.session
def check(session, reuse_venv=True):
    session.install("flake8", "isort==5.*", "black")
    session.run("flake8", "pdbr", "tests")
    session.run("black", "--check", "--diff", *SOURCE_FILES)
    session.run("isort", "--check", "--diff", *SOURCE_FILES)


@nox.session(python=["3.6", "3.7", "3.8"])
def test(session, reuse_venv=True):
    session.install("pytest", "pytest-cov", "rich")
    session.run("pytest", "--cov-report", "term-missing", "--cov=pdbr", "tests")
