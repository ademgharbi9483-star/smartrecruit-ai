"""
SmartRecruit AI — Tests APIs Authentification
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def candidat_data():
    return {
        "email":      "candidat@test.com",
        "first_name": "Alice",
        "last_name":  "Dupont",
        "role":       "candidat",
        "password":   "SecurePass123!",
        "password2":  "SecurePass123!",
    }


@pytest.fixture
def recruteur_data():
    return {
        "email":      "recruteur@test.com",
        "first_name": "Bob",
        "last_name":  "Martin",
        "role":       "recruteur",
        "password":   "SecurePass123!",
        "password2":  "SecurePass123!",
    }


@pytest.mark.django_db
class TestRegister:
    def test_register_candidat_success(self, api_client, candidat_data):
        response = api_client.post('/api/v1/auth/register/', candidat_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['user']['email'] == candidat_data['email']
        assert response.data['user']['role'] == 'candidat'

    def test_register_recruteur_success(self, api_client, recruteur_data):
        response = api_client.post('/api/v1/auth/register/', recruteur_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_register_duplicate_email(self, api_client, candidat_data):
        api_client.post('/api/v1/auth/register/', candidat_data, format='json')
        response = api_client.post('/api/v1/auth/register/', candidat_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_mismatch(self, api_client, candidat_data):
        candidat_data['password2'] = 'WrongPassword!'
        response = api_client.post('/api/v1/auth/register/', candidat_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_admin_forbidden(self, api_client, candidat_data):
        candidat_data['role'] = 'admin'
        response = api_client.post('/api/v1/auth/register/', candidat_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    def test_login_success(self, api_client, candidat_data):
        api_client.post('/api/v1/auth/register/', candidat_data, format='json')
        response = api_client.post('/api/v1/auth/login/', {
            "email": candidat_data['email'],
            "password": candidat_data['password'],
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data

    def test_login_wrong_password(self, api_client, candidat_data):
        api_client.post('/api/v1/auth/register/', candidat_data, format='json')
        response = api_client.post('/api/v1/auth/login/', {
            "email": candidat_data['email'],
            "password": "WrongPassword!",
        }, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, api_client):
        response = api_client.post('/api/v1/auth/login/', {
            "email": "nobody@test.com",
            "password": "SomePass123!",
        }, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProfile:
    def test_get_profile_authenticated(self, api_client, candidat_data):
        api_client.post('/api/v1/auth/register/', candidat_data, format='json')
        login = api_client.post('/api/v1/auth/login/', {
            "email": candidat_data['email'],
            "password": candidat_data['password'],
        }, format='json')
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = api_client.get('/api/v1/auth/me/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == candidat_data['email']

    def test_get_profile_unauthenticated(self, api_client):
        response = api_client.get('/api/v1/auth/me/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
