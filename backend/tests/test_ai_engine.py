"""
SmartRecruit AI — Tests Moteur IA (NLP, Scoring, Chatbot)
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status

from apps.ai_engine.services.scoring import compute_compatibility_score, rank_applications
from apps.ai_engine.services.nlp_extractor import extract_entities, _extract_email, _extract_phone, _extract_skills
from apps.ai_engine.services.chatbot import get_chatbot_response, FAQ_ENTRIES
from apps.ai_engine.services.summarizer import generate_profile_summary, generate_short_summary


# ── Tests Extraction NLP ────────────────────────────────────────────────────────

class TestNLPExtraction:
    def test_extract_email(self):
        text = "Contact: alice.dupont@email.com | Tel: +216 22 123 456"
        email = _extract_email(text)
        assert email == "alice.dupont@email.com"

    def test_extract_phone(self):
        text = "Téléphone : +216 22 123 456"
        phone = _extract_phone(text)
        assert phone is not None
        assert len(phone) > 0

    def test_extract_skills(self):
        text = (
            "Compétences : Python, Django, React, PostgreSQL, Docker, "
            "Machine Learning, JavaScript, AWS"
        )
        skills = _extract_skills(text)
        assert "Python" in skills
        assert "Django" in skills
        assert "React" in skills
        assert "PostgreSQL" in skills
        assert "Docker" in skills

    def test_extract_entities_full(self):
        text = (
            "Alice Dupont\n"
            "alice.dupont@email.com\n"
            "+216 22 123 456\n"
            "Tunis\n\n"
            "Compétences : Python, Django, React, PostgreSQL, Docker\n\n"
            "Formation : Master Informatique, 2022\n\n"
            "Expérience : Développeur Python chez TechCorp, 2022-2024\n\n"
            "Langues : Français, Anglais"
        )
        result = extract_entities(text)
        assert result['email'] == "alice.dupont@email.com"
        assert len(result['skills']) > 0
        assert "Python" in result['skills']
        assert len(result['education']) > 0
        assert len(result['experience']) > 0
        assert "Français" in result['languages']


# ── Tests Scoring ────────────────────────────────────────────────────────────────

class TestScoring:
    def test_perfect_match(self):
        cv_data = {
            'skills': ['Python', 'Django', 'PostgreSQL', 'Docker', 'React'],
            'education': [{'degree': 'Master', 'institution': '', 'year': '2022'}],
            'experience': [
                {'company': 'TechCorp', 'position': 'Dev', 'duration': '3 ans', 'description': ''}
            ],
        }
        job_offer = {
            'required_skills': ['Python', 'Django', 'PostgreSQL', 'Docker'],
            'experience_level': 'mid',
            'title': 'Dev Python',
            'description': 'Description',
        }
        result = compute_compatibility_score(cv_data, job_offer)
        assert result['global_score'] >= 70
        assert len(result['matched_skills']) == 4
        assert len(result['missing_skills']) == 0

    def test_no_skills_match(self):
        cv_data = {
            'skills': ['Photoshop', 'Illustrator', 'Marketing'],
            'education': [],
            'experience': [],
        }
        job_offer = {
            'required_skills': ['Python', 'Django', 'PostgreSQL'],
            'experience_level': 'senior',
            'title': 'Dev Python',
            'description': '',
        }
        result = compute_compatibility_score(cv_data, job_offer)
        assert result['global_score'] < 50
        assert len(result['missing_skills']) == 3

    def test_partial_match(self):
        cv_data = {
            'skills': ['Python', 'Java', 'MySQL'],
            'education': [{'degree': 'Licence'}],
            'experience': [{'position': 'Dev', 'company': 'X', 'duration': '2 ans'}],
        }
        job_offer = {
            'required_skills': ['Python', 'Django', 'React', 'Docker'],
            'experience_level': 'mid',
            'title': 'Dev',
            'description': '',
        }
        result = compute_compatibility_score(cv_data, job_offer)
        assert 0 < result['global_score'] < 100
        assert "Python" in result['matched_skills']
        assert "Django" in result['missing_skills']

    def test_score_within_bounds(self):
        for _ in range(10):
            cv_data = {
                'skills': ['Python'],
                'education': [{'degree': 'Master'}],
                'experience': [{'position': 'Dev'}],
            }
            job_offer = {
                'required_skills': ['Python', 'Django'],
                'experience_level': 'junior',
                'title': 'Dev',
                'description': '',
            }
            result = compute_compatibility_score(cv_data, job_offer)
            assert 0 <= result['global_score'] <= 100

    def test_rank_applications(self):
        apps = [
            {'id': 1, 'compatibility_score': 45},
            {'id': 2, 'compatibility_score': 90},
            {'id': 3, 'compatibility_score': 70},
        ]
        ranked = rank_applications(apps)
        assert ranked[0]['id'] == 2  # 90 en premier
        assert ranked[1]['id'] == 3  # 70
        assert ranked[2]['id'] == 1  # 45
        assert ranked[0]['rank'] == 1
        assert ranked[2]['rank'] == 3


# ── Tests Chatbot ─────────────────────────────────────────────────────────────────

class TestChatbot:
    def test_greeting(self):
        result = get_chatbot_response("bonjour")
        assert result['needs_escalation'] is False
        assert len(result['answer']) > 0

    def test_status_question(self):
        result = get_chatbot_response("quel est le statut de ma candidature ?")
        assert result['needs_escalation'] is False
        assert 'candidature' in result['answer'].lower()

    def test_how_to_apply(self):
        result = get_chatbot_response("comment postuler à une offre ?")
        assert result['needs_escalation'] is False

    def test_score_question(self):
        result = get_chatbot_response("comment est calculé mon score de compatibilité ?")
        assert result['needs_escalation'] is False
        assert 'score' in result['answer'].lower()

    def test_personalized_status(self):
        context = {
            'applications': [
                {'job_title': 'Dev Python', 'status': 'analyzing',
                 'status_display': 'En cours d\'analyse', 'compatibility_score': 75}
            ]
        }
        result = get_chatbot_response("statut de ma candidature", user_context=context)
        assert result['needs_escalation'] is False
        assert 'Dev Python' in result['answer']

    def test_empty_message(self):
        result = get_chatbot_response("")
        assert result['needs_escalation'] is False
        assert 'reformuler' in result['answer'].lower()

    def test_unknown_question_escalates(self):
        result = get_chatbot_response("xyzabc qwerty asdfgh")
        # Avec un message sans aucun mot-clé connu, ça devrait escalader
        assert result['confidence'] < 0.5


# ── Tests Résumé ──────────────────────────────────────────────────────────────────

class TestSummarizer:
    def test_generate_profile_summary(self):
        cv_data = {
            'name': 'Alice Dupont',
            'email': 'alice@test.com',
            'location': 'Tunis',
            'skills': ['Python', 'Django'],
            'education': [{'degree': 'Master', 'institution': 'Univ', 'year': '2022'}],
            'experience': [{'company': 'TechCorp', 'position': 'Dev', 'duration': '2 ans'}],
            'languages': ['Français', 'Anglais'],
        }
        job_offer = {'title': 'Dev Python', 'required_skills': ['Python', 'Django']}
        score_data = {
            'global_score': 85,
            'skills_score': 90,
            'experience_score': 80,
            'education_score': 85,
            'matched_skills': ['Python', 'Django'],
            'missing_skills': [],
        }
        summary = generate_profile_summary(cv_data, job_offer, score_data)
        assert 'Alice Dupont' in summary
        assert '85/100' in summary
        assert 'Python' in summary

    def test_generate_short_summary(self):
        cv_data = {'name': 'Alice Dupont'}
        score_data = {
            'global_score': 75,
            'matched_skills': ['Python', 'Django'],
            'missing_skills': ['React'],
        }
        short = generate_short_summary(cv_data, score_data)
        assert 'Alice Dupont' in short
        assert '75' in short


# ── Tests API Chatbot ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestChatbotAPI:
    def test_chatbot_endpoint(self, db):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(
            email="candidat@test.com",
            first_name="Alice", last_name="Dupont",
            role="candidat", password="SecurePass123!"
        )
        client = APIClient()
        login = client.post('/api/v1/auth/login/', {
            "email": "candidat@test.com", "password": "SecurePass123!"
        }, format='json')
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        response = client.post('/api/v1/ai/chatbot/', {
            "message": "Bonjour, comment déposer mon CV ?"
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'answer' in response.data
        assert len(response.data['answer']) > 0

    def test_chatbot_unauthenticated(self):
        client = APIClient()
        response = client.post('/api/v1/ai/chatbot/', {
            "message": "Bonjour"
        }, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
