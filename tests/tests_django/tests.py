from django.test import TestCase


class DjangoTest(TestCase):
    def test_runner(self):
        self.assertEqual("foo", "foo")
