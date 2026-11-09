"""
SmartRecruit AI — Calcul du score de compatibilité CV / Offre.

Stratégie :
  1. Sentence-BERT si disponible (embeddings sémantiques + similarité cosinus)
  2. TF-IDF + similarité cosinus avec scikit-learn si Sentence-BERT indisponible
  3. Fallback par correspondance de mots-clés (toujours disponible)

Le score global (0-100) combine :
  - skills_score     : correspondance des compétences (poids 60%)
  - experience_score : niveau d'expérience (poids 25%)
  - education_score   : niveau de formation (poids 15%)
"""

import math
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# ── Tentative d'import Sentence-BERT ─────────────────────────────────────────────
try:
    from sentence_transformers import SentenceTransformer, util
    _HAS_SBERT = True
except ImportError:
    _HAS_SBERT = False
    logger.info("Sentence-BERT non disponible — fallback TF-IDF / mots-clés.")

# ── Tentative d'import scikit-learn ──────────────────────────────────────────────
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False

_SBERT_MODEL = None


def _get_sbert_model():
    """Charge le modèle Sentence-BERT une seule fois."""
    global _SBERT_MODEL
    if _SBERT_MODEL is not None:
        return _SBERT_MODEL

    if not _HAS_SBERT:
        return None

    for model_name in ('all-MiniLM-L6-v2', 'paraphrase-multilingual-MiniLM-L12-v2'):
        try:
            _SBERT_MODEL = SentenceTransformer(model_name)
            logger.info(f"Modèle Sentence-BERT chargé : {model_name}")
            return _SBERT_MODEL
        except Exception as exc:
            logger.warning(f"Échec chargement {model_name} : {exc}")
            continue

    logger.info("Aucun modèle Sentence-BERT disponible — fallback TF-IDF.")
    return None


# ═══════════════════════════════════════════════════════════════════════════════
#  FONCTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

def compute_compatibility_score(
    cv_data: Dict,
    job_offer: Dict,
) -> Dict:
    """
    Calcule le score de compatibilité entre un CV et une offre d'emploi.

    Args:
        cv_data: dict avec keys 'skills', 'education', 'experience', 'summary'
        job_offer: dict avec keys 'required_skills', 'experience_level',
                   'title', 'description'

    Returns:
        {
            "global_score": float,         # 0-100
            "skills_score": float,
            "experience_score": float,
            "education_score": float,
            "matched_skills": [str, ...],
            "missing_skills": [str, ...],
            "method": str,                  # "sbert" | "tfidf" | "keyword"
            "summary": str,
        }
    """
    # ── Correspondance des compétences ────────────────────────────────────────────
    skills_score, matched, missing = _score_skills(cv_data, job_offer)

    # ── Score d'expérience ────────────────────────────────────────────────────────
    experience_score = _score_experience(cv_data, job_offer)

    # ── Score de formation ────────────────────────────────────────────────────────
    education_score = _score_education(cv_data, job_offer)

    # ── Score global pondéré ──────────────────────────────────────────────────────
    global_score = round(
        skills_score * 0.60 +
        experience_score * 0.25 +
        education_score * 0.15
    )
    global_score = max(0, min(100, global_score))

    # ── Résumé ────────────────────────────────────────────────────────────────────
    summary_parts = [
        f"Score global : {global_score}/100",
        f"Compétences : {skills_score:.0f}% ({len(matched)} correspondantes, {len(missing)} manquantes)",
        f"Expérience : {experience_score:.0f}%",
        f"Formation : {education_score:.0f}%",
    ]
    if missing:
        summary_parts.append(f"Compétences manquantes : {', '.join(missing[:5])}")

    return {
        "global_score": global_score,
        "skills_score": round(skills_score, 2),
        "experience_score": round(experience_score, 2),
        "education_score": round(education_score, 2),
        "matched_skills": matched,
        "missing_skills": missing,
        "method": _get_method_used(),
        "summary": " | ".join(summary_parts),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  SOUS-FONCTIONS DE SCORING
# ═══════════════════════════════════════════════════════════════════════════════

def _score_skills(cv_data: Dict, job_offer: Dict) -> Tuple[float, List[str], List[str]]:
    """
    Calcule le score de correspondance des compétences.
    Retourne (score 0-100, matched_skills, missing_skills).
    """
    cv_skills = [s.lower().strip() for s in cv_data.get('skills', []) if s]
    required_skills = [s.lower().strip() for s in job_offer.get('required_skills', []) if s]

    if not required_skills:
        return 50.0, [], []

    if not cv_skills:
        return 0.0, [], required_skills

    # Original casing of required skills for display
    orig_required = {s.lower().strip(): s for s in job_offer.get('required_skills', []) if s}

    # ── Correspondance exacte (mots-clés) ──────────────────────────────────────
    cv_skills_set = set(cv_skills)
    matched = []
    missing = []
    for skill_lower in required_skills:
        display_name = orig_required.get(skill_lower, skill_lower)
        if skill_lower in cv_skills_set:
            matched.append(display_name)
        else:
            # Correspondance partielle (inclusion de sous-chaîne)
            partial_match = any(
                skill_lower in cs or cs in skill_lower for cs in cv_skills
            )
            if partial_match:
                matched.append(display_name)
            else:
                missing.append(display_name)

    exact_score = (len(matched) / len(required_skills)) * 100

    # ── Enrichissement sémantique si Sentence-BERT disponible ─────────────────────
    sbert = _get_sbert_model()
    if sbert:
        try:
            semantic_score = _semantic_skill_score(sbert, cv_skills, required_skills)
            # Combine : 70% exact + 30% sémantique
            combined = exact_score * 0.7 + semantic_score * 0.3
            return combined, matched, missing
        except Exception as exc:
            logger.warning(f"Échec scoring sémantique : {exc}")

    # ── Fallback TF-IDF ───────────────────────────────────────────────────────────
    if _HAS_SKLEARN and cv_skills and required_skills:
        try:
            tfidf_score = _tfidf_skill_score(cv_skills, required_skills)
            combined = exact_score * 0.7 + tfidf_score * 0.3
            return combined, matched, missing
        except Exception as exc:
            logger.warning(f"Échec scoring TF-IDF : {exc}")

    # ── Fallback mots-clés uniquement ──────────────────────────────────────────
    return exact_score, matched, missing


def _semantic_skill_score(sbert_model, cv_skills: List[str], required_skills: List[str]) -> float:
    """Calcule un score sémantique avec Sentence-BERT."""
    # Embeddings
    cv_embeddings = sbert_model.encode(cv_skills, convert_to_tensor=True)
    req_embeddings = sbert_model.encode(required_skills, convert_to_tensor=True)

    # Similarité cosinus entre chaque compétence requise et les compétences du CV
    similarities = util.cos_sim(req_embeddings, cv_embeddings)

    # Pour chaque compétence requise, prendre la meilleure correspondance
    scores = []
    for i in range(len(required_skills)):
        best_sim = max(similarities[i].tolist())
        scores.append(float(best_sim))

    avg_score = sum(scores) / len(scores) * 100
    return max(0, min(100, avg_score))


def _tfidf_skill_score(cv_skills: List[str], required_skills: List[str]) -> float:
    """Calcule un score avec TF-IDF comme alternative légère."""
    all_skills = list(set(cv_skills + required_skills))
    documents = [' '.join(cv_skills), ' '.join(required_skills)]

    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform(documents)
    except ValueError:
        return 0.0

    sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return float(sim) * 100


def _score_experience(cv_data: Dict, job_offer: Dict) -> float:
    """Évalue la correspondance du niveau d'expérience."""
    experiences = cv_data.get('experience', [])
    num_experiences = len(experiences) if experiences else 0

    # Estimer les années d'expérience à partir du nombre d'expériences
    # (heuristique : ~1.5 ans par expérience en moyenne)
    estimated_years = num_experiences * 1.5

    required_level = job_offer.get('experience_level', 'mid')

    level_thresholds = {
        'junior': (0, 2),
        'mid': (2, 5),
        'senior': (5, 100),
    }

    min_years, max_years = level_thresholds.get(required_level, (2, 5))

    if estimated_years >= min_years:
        if estimated_years >= max_years:
            return 100.0
        else:
            # Progression proportionnelle
            progress = (estimated_years - min_years) / (max_years - min_years) if max_years > min_years else 1
            return 60 + progress * 40
    else:
        # En dessous du seuil minimum
        if min_years == 0:
            return 80.0
        ratio = estimated_years / min_years
        return max(20, ratio * 60)


def _score_education(cv_data: Dict, job_offer: Dict) -> float:
    """Évalue la correspondance de la formation."""
    education = cv_data.get('education', [])

    if not education:
        return 30.0  # Pas de formation détectée ne signifie pas pas de formation

    # Vérifier la présence d'un diplôme
    degrees = [e.get('degree', '') for e in education if e.get('degree')]

    if not degrees:
        return 50.0

    # Hiérarchie des diplômes
    degree_levels = {
        'Doctorat': 100, 'PhD': 100,
        'MBA': 95, 'DESS': 90, 'DEA': 90,
        'Master': 85, 'Mastère': 85, 'Engineering': 85,
        "Diplôme d'Ingénieur": 85,
        'Licence': 70, 'Bachelor': 70,
        'BTS': 60, 'DUT': 60,
        'DEUG': 50,
        'Baccalauréat': 40,
    }

    best_score = 50.0
    for degree in degrees:
        for key, score in degree_levels.items():
            if key.lower() in degree.lower():
                best_score = max(best_score, score)

    return best_score


def _get_method_used() -> str:
    """Retourne la méthode de scoring utilisée."""
    if _get_sbert_model():
        return "sbert"
    if _HAS_SKLEARN:
        return "tfidf"
    return "keyword"


# ═══════════════════════════════════════════════════════════════════════════════
#  CLASSEMENT DES CANDIDATURES
# ═══════════════════════════════════════════════════════════════════════════════

def rank_applications(applications: List[Dict]) -> List[Dict]:
    """
    Classe les candidatures par ordre décroissant de score de compatibilité.

    Args:
        applications: liste de dicts contenant au moins 'compatibility_score'.

    Returns:
        Liste triée par score décroissant, avec ajout du rang.
    """
    sorted_apps = sorted(
        applications,
        key=lambda a: a.get('compatibility_score') or 0,
        reverse=True,
    )
    for rank, app in enumerate(sorted_apps, start=1):
        app['rank'] = rank
    return sorted_apps
