"""
SmartRecruit AI — Génération de résumés de profils candidats.

Produit un résumé structuré et intelligible mettant en évidence :
  - Les informations clés (nom, contact, formation)
  - Les compétences correspondantes à l'offre
  - Les compétences manquantes
  - Un verdict global sur la compatibilité
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


def generate_profile_summary(cv_data: Dict, job_offer: Dict, score_data: Dict) -> str:
    """
    Génère un résumé textuel structuré du profil candidat.

    Args:
        cv_data: données extraites du CV (entités NLP)
        job_offer: données de l'offre d'emploi
        score_data: résultats du scoring (matched/missing skills, scores)

    Returns:
        Résumé formaté en plusieurs sections.
    """
    sections = []

    # ── En-tête : identité ────────────────────────────────────────────────────────
    name = cv_data.get('name', 'Candidat')
    email = cv_data.get('email', '')
    phone = cv_data.get('phone', '')
    location = cv_data.get('location', '')

    header_parts = [f"Profil de {name}"]
    if location:
        header_parts.append(f"Localisation : {location}")
    if email:
        header_parts.append(f"Email : {email}")
    if phone:
        header_parts.append(f"Téléphone : {phone}")
    sections.append(" — ".join(header_parts))

    # ── Score global ──────────────────────────────────────────────────────────────
    global_score = score_data.get('global_score', 0)
    verdict = _get_verdict(global_score)
    sections.append(f"\nScore de compatibilité : {global_score}/100 — {verdict}")

    # ── Détail des scores ──────────────────────────────────────────────────────────
    score_lines = []
    if 'skills_score' in score_data:
        score_lines.append(f"  • Compétences : {score_data['skills_score']:.0f}%")
    if 'experience_score' in score_data:
        score_lines.append(f"  • Expérience : {score_data['experience_score']:.0f}%")
    if 'education_score' in score_data:
        score_lines.append(f"  • Formation : {score_data['education_score']:.0f}%")
    if score_lines:
        sections.append("\nDétail des scores :\n" + "\n".join(score_lines))

    # ── Compétences correspondantes ────────────────────────────────────────────────
    matched = score_data.get('matched_skills', [])
    if matched:
        sections.append(f"\nCompétences correspondantes ({len(matched)}) :\n  • " + "\n  • ".join(matched))
    else:
        sections.append("\nAucune compétence correspondante détectée.")

    # ── Compétences manquantes ──────────────────────────────────────────────────────
    missing = score_data.get('missing_skills', [])
    if missing:
        sections.append(f"\nCompétences manquantes ({len(missing)}) :\n  • " + "\n  • ".join(missing))

    # ── Formation ──────────────────────────────────────────────────────────────────
    education = cv_data.get('education', [])
    if education:
        edu_lines = []
        for edu in education:
            parts = []
            if edu.get('degree'):
                parts.append(edu['degree'])
            if edu.get('institution'):
                parts.append(edu['institution'])
            if edu.get('year'):
                parts.append(edu['year'])
            if parts:
                edu_lines.append("  • " + " — ".join(parts))
        if edu_lines:
            sections.append("\nFormation :\n" + "\n".join(edu_lines))

    # ── Expérience ──────────────────────────────────────────────────────────────────
    experiences = cv_data.get('experience', [])
    if experiences:
        exp_lines = []
        for exp in experiences[:5]:
            parts = []
            if exp.get('position'):
                parts.append(exp['position'])
            if exp.get('company'):
                parts.append(exp['company'])
            if exp.get('duration'):
                parts.append(exp['duration'])
            if parts:
                exp_lines.append("  • " + " — ".join(parts))
        if exp_lines:
            sections.append(f"\nExpériences professionnelles ({len(experiences)} au total) :\n" + "\n".join(exp_lines))

    # ── Langues ──────────────────────────────────────────────────────────────────
    languages = cv_data.get('languages', [])
    if languages:
        sections.append("\nLangues : " + ", ".join(languages))

    # ── Recommandation ──────────────────────────────────────────────────────────────
    sections.append(f"\nRecommandation : {_get_recommendation(global_score)}")

    return "\n".join(sections)


def _get_verdict(score: int) -> str:
    """Retourne un libellé qualitatif selon le score."""
    if score >= 85:
        return "Excellente correspondance"
    elif score >= 70:
        return "Très bonne correspondance"
    elif score >= 55:
        return "Correspondance acceptable"
    elif score >= 40:
        return "Correspondance limitée"
    else:
        return "Correspondance faible"


def _get_recommendation(score: int) -> str:
    """Retourne une recommandation d'action selon le score."""
    if score >= 70:
        return "Candidat recommandé pour un entretien."
    elif score >= 50:
        return "Candidat à évaluer en entretien pour confirmer les compétences."
    else:
        return "Candidat ne correspondant pas aux critères principaux de l'offre."


def generate_short_summary(cv_data: Dict, score_data: Dict) -> str:
    """Version courte du résumé pour affichage rapide dans le tableau de bord."""
    name = cv_data.get('name', 'Candidat')
    score = score_data.get('global_score', 0)
    matched = len(score_data.get('matched_skills', []))
    missing = len(score_data.get('missing_skills', []))

    return (
        f"{name} — Score {score}/100 — "
        f"{matched} compétence(s) correspondante(s), "
        f"{missing} manquante(s). {_get_verdict(score)}."
    )
