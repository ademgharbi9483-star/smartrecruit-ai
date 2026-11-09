"""
SmartRecruit AI — Tests APIs Offres d'emploi
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
def recruteur(db):
    return User.objects.create_user(
        email="recruteur@test.com",
        first_name="Bob", last_name="Martin",
        role="recruteur", password="SecurePass123!"
    )


@pytest.fixture
def candidat(db):
    return User.objects.create_user(
        email="candidat@test.com",
        first_name="Alice", last_name="Dupont",
        role="candidat", password="SecurePass123!"
    )


@pytest.fixture
def auth_recruteur(recruteur):
    client = APIClient()
    response = client.post('/api/v1/auth/login/', {
        "email": "recruteur@test.com", "password": "SecurePass123!"
    }, format='json')
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


@pytest.fixture
def auth_candidat(candidat):
    client = APIClient()
    response = client.post('/api/v1/auth/login/', {
        "email": "candidat@test.com", "password": "SecurePass123!"
    }, format='json')
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


@pytest.fixture
def offre_data():
    return {
        "title":            "Développeur Python Senior",
        "description":      "Nous recherchons un développeur Python expérimenté.",
        "required_skills":  ["Python", "Django", "PostgreSQL", "Docker"],
        "location":         "Tunis",
        "contract_type":    "CDI",
        "experience_level": "senior",
        "sector":           "Informatique",
        "salary_min":       3000,
        "salary_max":       5000,
    }


@pytest.mark.django_db
class TestJobOfferCRUD:
    def test_create_offer_as_recruteur(self, auth_recruteur, offre_data):
        response = auth_recruteur.post('/api/v1/jobs/create/', offre_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == offre_data['title']
        assert response.data['location'] == 'Tunis'

    def test_create_offer_as_candidat_forbidden(self, auth_candidat, offre_data):
        response = auth_candidat.post('/api/v1/jobs/create/', offre_data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_offers_public(self, api_client, auth_recruteur, offre_data):
        auth_recruteur.post('/api/v1/jobs/create/', offre_data, format='json')
        response = api_client.get('/api/v1/jobs/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_get_offer_detail(self, api_client, auth_recruteur, offre_data):
        create_resp = auth_recruteur.post('/api/v1/jobs/create/', offre_data, format='json')
        offer_id = create_resp.data['id']
        response = api_client.get(f'/api/v1/jobs/{offer_id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == offer_id

    def test_update_own_offer(self, auth_recruteur, offre_data):
        create_resp = auth_recruteur.post('/api/v1/jobs/create/', offre_data, format='json')
        offer_id = create_resp.data['id']
        response = auth_recruteur.patch(
            f'/api/v1/jobs/{offer_id}/update/',
            {"title": "Dev Python Senior (mise à jour)"},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == "Dev Python Senior (mise à jour)"

    def test_delete_own_offer(self, auth_recruteur, offre_data):
        create_resp = auth_recruteur.post('/api/v1/jobs/create/', offre_data, format='json')
        offer_id = create_resp.data['id']
        response = auth_recruteur.delete(f'/api/v1/jobs/{offer_id}/delete/')
        assert response.status_code == status.HTTP_200_OK

    def test_close_offer(self, auth_recruteur, offre_data):
        create_resp = auth_recruteur.post('/api/v1/jobs/create/', offre_data, format='json')
        offer_id = create_resp.data['id']
        response = auth_recruteur.post(f'/api/v1/jobs/{offer_id}/close/')
        assert response.status_code == status.HTTP_200_OK

    def test_my_offers(self, auth_recruteur, offre_data):
        auth_recruteur.post('/api/v1/jobs/create/', offre_data, format='json')
        response = auth_recruteur.get('/api/v1/jobs/my-offers/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_create_offer_empty_skills_fails(self, auth_recruteur, offre_data):
        offre_data['required_skills'] = []
        response = auth_recruteur.post('/api/v1/jobs/create/', offre_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_salary_min_greater_than_max_fails(self, auth_recruteur, offre_data):
        offre_data['salary_min'] = 6000
        offre_data['salary_max'] = 3000
        response = auth_recruteur.post('/api/v1/jobs/create/', offre_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
