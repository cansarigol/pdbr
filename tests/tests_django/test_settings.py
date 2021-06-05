import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = "fake-key"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

INSTALLED_APPS = ("tests.tests_django",)

TEST_RUNNER = "pdbr.runner.PdbrDiscoverRunner"

ROOT_URLCONF = "tests.tests_django.urls"

MIDDLEWARE = ["pdbr.middleware.PdbrMiddleware"]
