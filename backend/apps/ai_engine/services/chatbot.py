"""
SmartRecruit AI — Chatbot RH

Chatbot basé sur un système de matching de questions fréquentes (FAQ)
avec scoring de similarité. Utilise TF-IDF si scikit-learn est disponible,
sinon un matching par mots-clés.

Peut répondre aux questions des candidats sur :
  - L'état de leur candidature
  - Les délais de traitement
  - Le profil requis pour une offre
  - Le processus de recrutement
  - Comment déposer un CV
"""

import re
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False


# ── Base de questions / réponses (FAQ) ──────────────────────────────────────────

FAQ_ENTRIES = [
    {
        "id": "status_application",
        "keywords": ["état", "statut", "candidature", "où", "progression", "suivi", "status"],
        "question": "Quel est l'état de ma candidature ?",
        "answer": (
            "Vous pouvez consulter l'état de votre candidature dans votre espace candidat, "
            "section « Mes candidatures ». Les statuts possibles sont : "
            "Reçue, En cours d'analyse, Examinée, Présélectionnée, Acceptée ou Refusée. "
            "Vous recevrez également une notification par email à chaque changement de statut."
        ),
    },
    {
        "id": "processing_time",
        "keywords": ["délai", "temps", "combien", "quand", "réponse", "attendre", "rapidement"],
        "question": "Combien de temps avant d'avoir une réponse ?",
        "answer": (
            "Le traitement de votre candidature par notre système IA prend moins de 30 secondes. "
            "Ensuite, le recruteur examine les candidatures classées. "
            "Vous recevrez généralement une première réponse sous 5 à 7 jours ouvrés."
        ),
    },
    {
        "id": "required_profile",
        "keywords": ["profil", "compétence", "requis", "qualification", "expérience", "diplôme"],
        "question": "Quel est le profil requis pour cette offre ?",
        "answer": (
            "Chaque offre d'emploi détaille les compétences requises, le niveau d'expérience "
            "et le type de contrat. Consultez la section « Compétences requises » de l'offre "
            "pour vérifier si votre profil correspond. Notre système IA calcule automatiquement "
            "un score de compatibilité entre votre CV et l'offre."
        ),
    },
    {
        "id": "how_to_apply",
        "keywords": ["postuler", "candidater", "déposer", "comment", "appliquer", "soumettre"],
        "question": "Comment postuler à une offre ?",
        "answer": (
            "Pour postuler : 1) Créez un compte candidat, 2) Uploadez votre CV au format PDF, "
            "3) Consultez les offres disponibles, 4) Cliquez sur « Postuler » sur l'offre "
            "qui vous intéresse. Votre CV sera automatiquement analysé par notre IA."
        ),
    },
    {
        "id": "upload_cv",
        "keywords": ["cv", "upload", "télécharger", "importer", "fichier", "pdf", "document"],
        "question": "Comment déposer mon CV ?",
        "answer": (
            "Rendez-vous dans votre espace candidat, section « Mon CV ». "
            "Cliquez sur « Télécharger un CV » et sélectionnez un fichier PDF (max 10 Mo). "
            "Le système extraira automatiquement vos informations (compétences, formations, "
            "expériences) grâce à notre module NLP."
        ),
    },
    {
        "id": "score_explanation",
        "keywords": ["score", "compatibilité", "correspondance", "classement", "pourcentage"],
        "question": "Comment est calculé mon score de compatibilité ?",
        "answer": (
            "Le score de compatibilité (0 à 100) est calculé par notre IA en comparant "
            "vos compétences extraites du CV avec les exigences de l'offre. "
            "Il prend en compte : les compétences (60%), l'expérience (25%) et la formation (15%). "
            "Plus le score est élevé, plus votre profil correspond à l'offre."
        ),
    },
    {
        "id": "improve_score",
        "keywords": ["améliorer", "augmenter", "score", "mieux", "optimiser", "augmenter"],
        "question": "Comment améliorer mon score de compatibilité ?",
        "answer": (
            "Pour améliorer votre score : 1) Mettez à jour votre CV avec vos compétences "
            "les plus récentes, 2) Mentionnez explicitement les compétences requises dans "
            "l'offre, 3) Détaillez vos expériences professionnelles avec les dates et "
            "technologies utilisées, 4) Ajoutez vos diplômes et certifications."
        ),
    },
    {
        "id": "multiple_applications",
        "keywords": ["plusieurs", "multi", "nombre", "limite", "offres", "postuler"],
        "question": "Puis-je postuler à plusieurs offres ?",
        "answer": (
            "Oui, vous pouvez postuler à autant d'offres que vous le souhaitez. "
            "Cependant, vous ne pouvez soumettre qu'une seule candidature par offre. "
            "Chaque candidature est évaluée indépendamment par notre IA."
        ),
    },
    {
        "id": "edit_profile",
        "keywords": ["modifier", "profil", "compte", "information", "mettre à jour", "changer"],
        "question": "Comment modifier mon profil ?",
        "answer": (
            "Rendez-vous dans votre espace candidat, section « Mon profil ». "
            "Vous pouvez y modifier vos informations personnelles, votre titre professionnel, "
            "votre résumé et vos liens (LinkedIn, GitHub, portfolio)."
        ),
    },
    {
        "id": "contact_recruiter",
        "keywords": ["contact", "recruteur", "parler", "humain", "échanger", "contacter"],
        "question": "Comment contacter un recruteur ?",
        "answer": (
            "Si vous avez une question complexe que je ne peux pas traiter, "
            "je vais transférer votre demande à un recruteur qui vous contactera par email. "
            "Vous pouvez aussi trouver les coordonnées du recruteur dans la description de l'offre."
        ),
    },
    {
        "id": "delete_account",
        "keywords": ["supprimer", "compte", "désactiver", "fermer", "effacer"],
        "question": "Comment supprimer mon compte ?",
        "answer": (
            "Pour supprimer votre compte, contactez l'administrateur via la page de contact. "
            "Vos données seront supprimées conformément au RGPD dans un délai de 30 jours."
        ),
    },
    {
        "id": "greeting",
        "keywords": ["bonjour", "salut", "hello", "hey", "bonsoir", "coucou", "hi"],
        "question": "Bonjour",
        "answer": (
            "Bonjour ! Je suis le chatbot RH de SmartRecruit AI. "
            "Je peux vous aider avec : l'état de votre candidature, le processus de recrutement, "
            "le dépôt de CV, le score de compatibilité, etc. "
            "Posez-moi votre question !"
        ),
    },
    {
        "id": "thanks",
        "keywords": ["merci", "thanks", "thank", "super", "génial"],
        "question": "Merci",
        "answer": "De rien ! N'hésitez pas si vous avez d'autres questions. Bonne chance pour vos candidatures !",
    },
]

# Seuil de similarité pour considérer une réponse comme pertinente
SIMILARITY_THRESHOLD = 0.15


# ═══════════════════════════════════════════════════════════════════════════════
#  FONCTION PRINCIPALE DU CHATBOT
# ═══════════════════════════════════════════════════════════════════════════════

def get_chatbot_response(
    user_message: str,
    user_context: Optional[Dict] = None,
) -> Dict:
    """
    Génère une réponse à la question d'un candidat.

    Args:
        user_message: question du candidat
        user_context: contexte optionnel (candidate_id, applications, etc.)

    Returns:
        {
            "answer": str,
            "matched_question": str | None,
            "confidence": float,
            "needs_escalation": bool,
        }
    """
    if not user_message or not user_message.strip():
        return {
            "answer": "Je n'ai pas compris votre question. Pourriez-vous reformuler ?",
            "matched_question": None,
            "confidence": 0.0,
            "needs_escalation": False,
        }

    # ── Recherche de la meilleure correspondance ────────────────────────────────
    best_entry = None
    best_score = 0.0

    if _HAS_SKLEARN:
        best_entry, best_score = _match_with_tfidf(user_message)
    else:
        best_entry, best_score = _match_with_keywords(user_message)

    # ── Réponse personnalisée si on a du contexte sur les candidatures ──────────
    if best_entry and best_entry["id"] == "status_application" and user_context:
        personalized = _personalize_status_response(user_context)
        if personalized:
            return {
                "answer": personalized,
                "matched_question": best_entry["question"],
                "confidence": max(best_score, 0.8),
                "needs_escalation": False,
            }

    # ── Réponse trouvée ──────────────────────────────────────────────────────────
    if best_entry and best_score >= SIMILARITY_THRESHOLD:
        return {
            "answer": best_entry["answer"],
            "matched_question": best_entry["question"],
            "confidence": round(best_score, 3),
            "needs_escalation": False,
        }

    # ── Aucune correspondance → escalade ──────────────────────────────────────────
    return {
        "answer": (
            "Je n'ai pas trouvé de réponse à votre question dans ma base de connaissances. "
            "Je transfère votre demande à un recruteur qui vous répondra par email. "
            "En attendant, vous pouvez consulter la FAQ ou votre espace candidat."
        ),
        "matched_question": None,
        "confidence": 0.0,
        "needs_escalation": True,
    }


# ── Matching TF-IDF ───────────────────────────────────────────────────────────

_vectorizer = None
_tfidf_matrix = None

def _match_with_tfidf(user_message: str):
    """Matching par similarité TF-IDF cosinus."""
    global _vectorizer, _tfidf_matrix

    questions = [entry["question"] for entry in FAQ_ENTRIES]
    documents = questions + [user_message]

    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(documents)
    except ValueError:
        return _match_with_keywords(user_message)

    # Similarité entre la question utilisateur et chaque FAQ
    user_vec = tfidf_matrix[-1:]
    similarities = cosine_similarity(user_vec, tfidf_matrix[:-1])[0]

    best_idx = similarities.argmax()
    best_score = float(similarities[best_idx])

    return FAQ_ENTRIES[best_idx], best_score


# ── Matching par mots-clés (fallback) ──────────────────────────────────────────

def _match_with_keywords(user_message: str):
    """Matching par comptage de mots-clés communs."""
    message_lower = user_message.lower()
    message_words = set(re.findall(r'\b\w+\b', message_lower))

    best_entry = None
    best_score = 0.0

    for entry in FAQ_ENTRIES:
        keywords = set(k.lower() for k in entry["keywords"])
        # Score = nombre de mots-clés présents / nombre total de mots-clés
        overlap = message_words & keywords
        if not overlap:
            continue
        score = len(overlap) / len(keywords)

        # Bonus si les mots-clés apparaissent directement
        for kw in entry["keywords"]:
            if kw.lower() in message_lower:
                score += 0.1

        if score > best_score:
            best_score = score
            best_entry = entry

    return best_entry, min(best_score, 1.0)


# ── Personnalisation des réponses ──────────────────────────────────────────────

def _personalize_status_response(user_context: Dict) -> Optional[str]:
    """Génère une réponse personnalisée sur l'état des candidatures."""
    applications = user_context.get('applications', [])
    if not applications:
        return (
            "Vous n'avez pas encore de candidature en cours. "
            "Consultez les offres disponibles et postulez avec votre CV !"
        )

    lines = [f"Vous avez {len(applications)} candidature(s) en cours :"]
    for app in applications[:5]:
        status_label = app.get('status_display', app.get('status', ''))
        title = app.get('job_title', 'Offre')
        score = app.get('compatibility_score')
        score_str = f" (score: {score}/100)" if score else ""
        lines.append(f"  • {title} — Statut : {status_label}{score_str}")

    return "\n".join(lines)
