from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from user.models import Client


class TestIdentifyEndpoint(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.url = '/user/client/identify/'

    def test_creates_new_client(self):
        response = self.api_client.post(
            self.url,
            {'install_id': 'test-device-001'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['install_id'], 'test-device-001')
        self.assertEqual(Client.objects.count(), 1)

    def test_creates_client_with_label(self):
        response = self.api_client.post(
            self.url,
            {'install_id': 'test-device-002', 'label': 'My Phone'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['label'], 'My Phone')

    def test_returns_existing_client(self):
        Client.objects.create(install_id='existing-device')

        response = self.api_client.post(
            self.url,
            {'install_id': 'existing-device'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['install_id'], 'existing-device')
        self.assertEqual(Client.objects.count(), 1)

    def test_requires_install_id(self):
        response = self.api_client.post(self.url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_response_contains_all_fields(self):
        response = self.api_client.post(
            self.url,
            {'install_id': 'test-device-003'},
            format='json',
        )

        self.assertIn('install_id', response.data)
        self.assertIn('label', response.data)
        self.assertIn('created_at', response.data)
        self.assertIn('last_seen_at', response.data)


class TestMeEndpoint(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.url = '/user/client/me/'

    def test_get_returns_client(self):
        Client.objects.create(install_id='my-device', label='Test Device')

        response = self.api_client.get(
            self.url,
            HTTP_X_INSTALL_ID='my-device',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['install_id'], 'my-device')
        self.assertEqual(response.data['label'], 'Test Device')

    def test_get_requires_header(self):
        response = self.api_client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_get_returns_404_for_nonexistent(self):
        response = self.api_client.get(
            self.url,
            HTTP_X_INSTALL_ID='nonexistent',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_removes_client(self):
        Client.objects.create(install_id='delete-me')

        response = self.api_client.delete(
            self.url,
            HTTP_X_INSTALL_ID='delete-me',
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Client.objects.count(), 0)

    def test_delete_requires_header(self):
        response = self.api_client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_returns_404_for_nonexistent(self):
        response = self.api_client.delete(
            self.url,
            HTTP_X_INSTALL_ID='nonexistent',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
