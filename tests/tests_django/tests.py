from django.test import TestCase


class DjangoTest(TestCase):
    def test_runner(self):
        self.assertEqual("foo", "foo")

    def test_middleware(self):
        response = self.client.get("")
        self.assertEqual(response.status_code, 200)
