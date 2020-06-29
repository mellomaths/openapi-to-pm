from django.test import SimpleTestCase

# Create your tests here.

class PostmanTests(SimpleTestCase):
    def test_homepage_status_code(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
