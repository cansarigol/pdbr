from pathlib import Path

BASE_DIR = Path(__file__).absolute().parents[1]

SECRET_KEY = "fake-key"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "db.sqlite3"),
    }
}

INSTALLED_APPS = ("tests.tests_django",)

TEST_RUNNER = "pdbr.runner.PdbrDiscoverRunner"

ROOT_URLCONF = "tests.tests_django.urls"

MIDDLEWARE = ["pdbr.middleware.PdbrMiddleware"]
