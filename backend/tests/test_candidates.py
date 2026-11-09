"""
SmartRecruit AI — Tests APIs Candidatures et CV
"""

import io
from django.core.files.uploadedfile import SimpleUploadedFile

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


# ── Fixtures ────────────────────────────────────────────────────────────────────

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
def auth_candidat(candidat):
    client = APIClient()
    response = client.post('/api/v1/auth/login/', {
        "email": "candidat@test.com", "password": "SecurePass123!"
    }, format='json')
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


@pytest.fixture
def auth_recruteur(recruteur):
    client = APIClient()
    response = client.post('/api/v1/auth/login/', {
        "email": "recruteur@test.com", "password": "SecurePass123!"
    }, format='json')
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


@pytest.fixture
def job_offer(recruteur):
    from apps.jobs.models import JobOffer
    return JobOffer.objects.create(
        recruiter=recruteur,
        title="Développeur Python Senior",
        description="Nous recherchons un développeur Python expérimenté.",
        required_skills=["Python", "Django", "PostgreSQL", "Docker"],
        location="Tunis",
        contract_type="CDI",
        experience_level="senior",
        sector="Informatique",
        salary_min=3000,
        salary_max=5000,
    )


@pytest.fixture
def fake_pdf():
    """Génère un faux fichier PDF pour les tests d'upload."""
    # En-tête PDF minimal valide
    pdf_content = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
    return SimpleUploadedFile(
        "cv_test.pdf", pdf_content, content_type="application/pdf"
    )


# ── Tests Profil Candidat ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCandidateProfile:
    def test_get_or_create_profile(self, auth_candidat):
        response = auth_candidat.get('/api/v1/candidates/profile/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == "candidat@test.com"

    def test_update_profile(self, auth_candidat):
        response = auth_candidat.patch('/api/v1/candidates/profile/', {
            "headline": "Développeuse Python",
            "location": "Sousse",
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['headline'] == "Développeuse Python"

    def test_profile_forbidden_for_recruteur(self, auth_recruteur):
        response = auth_recruteur.get('/api/v1/candidates/profile/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ── Tests CV Upload ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCVUpload:
    def test_upload_cv_pdf(self, auth_candidat, fake_pdf):
        response = auth_candidat.post(
            '/api/v1/candidates/cvs/upload/',
            {'file': fake_pdf, 'is_primary': True},
            format='multipart'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['original_name'] == 'cv_test.pdf'

    def test_upload_non_pdf_rejected(self, auth_candidat):
        txt_file = SimpleUploadedFile("cv.txt", b"hello", content_type="text/plain")
        response = auth_candidat.post(
            '/api/v1/candidates/cvs/upload/',
            {'file': txt_file},
            format='multipart'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_my_cvs(self, auth_candidat, fake_pdf):
        auth_candidat.post(
            '/api/v1/candidates/cvs/upload/',
            {'file': fake_pdf},
            format='multipart'
        )
        response = auth_candidat.get('/api/v1/candidates/cvs/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_delete_cv(self, auth_candidat, fake_pdf):
        upload = auth_candidat.post(
            '/api/v1/candidates/cvs/upload/',
            {'file': fake_pdf},
            format='multipart'
        )
        cv_id = upload.data['id']
        response = auth_candidat.delete(f'/api/v1/candidates/cvs/{cv_id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT


# ── Tests Candidatures ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestApplications:
    def test_apply_to_job(self, auth_candidat, job_offer, fake_pdf):
        # D'abord uploader un CV
        cv_resp = auth_candidat.post(
            '/api/v1/candidates/cvs/upload/',
            {'file': fake_pdf, 'is_primary': True},
            format='multipart'
        )
        cv_id = cv_resp.data['id']

        # Puis postuler
        response = auth_candidat.post('/api/v1/candidates/applications/', {
            "job_offer": job_offer.id,
            "cv": cv_id,
            "cover_letter": "Je suis très intéressé par ce poste.",
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_duplicate_application_fails(self, auth_candidat, job_offer, fake_pdf):
        cv_resp = auth_candidat.post(
            '/api/v1/candidates/cvs/upload/',
            {'file': fake_pdf},
            format='multipart'
        )
        cv_id = cv_resp.data['id']
        auth_candidat.post('/api/v1/candidates/applications/', {
            "job_offer": job_offer.id, "cv": cv_id,
        }, format='json')
        response = auth_candidat.post('/api/v1/candidates/applications/', {
            "job_offer": job_offer.id, "cv": cv_id,
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_my_applications(self, auth_candidat, job_offer, fake_pdf):
        cv_resp = auth_candidat.post(
            '/api/v1/candidates/cvs/upload/',
            {'file': fake_pdf},
            format='multipart'
        )
        auth_candidat.post('/api/v1/candidates/applications/', {
            "job_offer": job_offer.id, "cv": cv_resp.data['id'],
        }, format='json')
        response = auth_candidat.get('/api/v1/candidates/applications/mine/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1


# ── Tests Recruteur — Candidatures par offre ─────────────────────────────────────

@pytest.mark.django_db
class TestRecruiterApplications:
    def _create_application(self, auth_candidat, job_offer, fake_pdf):
        cv_resp = auth_candidat.post(
            '/api/v1/candidates/cvs/upload/',
            {'file': fake_pdf},
            format='multipart'
        )
        auth_candidat.post('/api/v1/candidates/applications/', {
            "job_offer": job_offer.id, "cv": cv_resp.data['id'],
        }, format='json')

    def test_list_job_applications(self, auth_recruteur, auth_candidat, job_offer, fake_pdf):
        self._create_application(auth_candidat, job_offer, fake_pdf)
        response = auth_recruteur.get(f'/api/v1/candidates/jobs/{job_offer.id}/applications/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_update_application_status(self, auth_recruteur, auth_candidat, job_offer, fake_pdf):
        self._create_application(auth_candidat, job_offer, fake_pdf)
        apps = auth_recruteur.get(f'/api/v1/candidates/jobs/{job_offer.id}/applications/')
        app_id = apps.data['results'][0]['id']

        response = auth_recruteur.patch(f'/api/v1/candidates/applications/{app_id}/status/', {
            "status": "shortlisted",
            "recruiter_notes": "Bon profil",
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'shortlisted'

    def test_candidat_cannot_access_job_applications(self, auth_candidat, job_offer, fake_pdf):
        self._create_application(auth_candidat, job_offer, fake_pdf)
        response = auth_candidat.get(f'/api/v1/candidates/jobs/{job_offer.id}/applications/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ── Tests Tableau de bord ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDashboard:
    def test_recruiter_dashboard(self, auth_recruteur, job_offer):
        response = auth_recruteur.get('/api/v1/candidates/dashboard/')
        assert response.status_code == status.HTTP_200_OK
        assert 'global' in response.data
        assert 'by_status' in response.data
        assert 'jobs_summary' in response.data

    def test_candidat_cannot_access_dashboard(self, auth_candidat):
        response = auth_candidat.get('/api/v1/candidates/dashboard/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
