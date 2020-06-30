import nox

@nox.session
def lint(session, reuse_venv=True):
    session.install('autoflake', 'isort', 'black')
    session.run('autoflake', "--in-place", "--recursive", 'pdbr', 'tests')
    session.run('black', 'pdbr', 'tests')
    session.run('isort', '--recursive', 'pdbr', 'tests')


@nox.session
def check(session, reuse_venv=True):
    session.install('flake8', 'isort', 'black')
    session.run('flake8', 'pdbr', 'tests')
    session.run("black", "--check", "--diff", 'pdbr', 'tests')
    session.run('isort', "--check", "--diff", '--recursive', 'pdbr', 'tests')


@nox.session(python=["3.6", "3.7", "3.8"])
def test(session, reuse_venv=True):
    session.install('pytest', 'rich')
    session.run('pytest')