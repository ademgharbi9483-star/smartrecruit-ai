"""
SmartRecruit AI — Extraction de texte depuis les fichiers PDF.

Utilise PyMuPDF (fitz) en priorité. Un fallback basé sur pdfplumber
peut être activé si disponible.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Tentative d'import de PyMuPDF
try:
    import fitz  # PyMuPDF
    _HAS_FITZ = True
except ImportError:
    _HAS_FITZ = False
    logger.warning("PyMuPDF non disponible — l'extraction PDF sera limitée.")

# Tentative d'import de pdfplumber (fallback)
try:
    import pdfplumber
    _HAS_PDFPLUMBER = True
except ImportError:
    _HAS_PDFPLUMBER = False


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extrait le texte brut depuis un fichier PDF.

    Args:
        file_path: chemin vers le fichier PDF.

    Returns:
        Texte brut extrait, nettoyé. Retourne une chaîne vide en cas d'échec.
    """
    if not os.path.exists(file_path):
        logger.error(f"Fichier introuvable : {file_path}")
        return ""

    text = ""

    # ── Tentative 1 : PyMuPDF ──────────────────────────────────────────────────
    if _HAS_FITZ:
        try:
            text = _extract_with_fitz(file_path)
            if text.strip():
                return _clean_text(text)
        except Exception as exc:
            logger.warning(f"Échec PyMuPDF sur {file_path} : {exc}")

    # ── Tentative 2 : pdfplumber ────────────────────────────────────────────────
    if _HAS_PDFPLUMBER:
        try:
            text = _extract_with_pdfplumber(file_path)
            if text.strip():
                return _clean_text(text)
        except Exception as exc:
            logger.warning(f"Échec pdfplumber sur {file_path} : {exc}")

    # ── Aucune librairie disponible ──────────────────────────────────────────────
    if not _HAS_FITZ and not _HAS_PDFPLUMBER:
        logger.error(
            "Aucune librairie d'extraction PDF disponible. "
            "Installez PyMuPDF : pip install PyMuPDF"
        )

    return ""


def _extract_with_fitz(file_path: str) -> str:
    """Extraction avec PyMuPDF."""
    text_parts = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text_parts.append(page.get_text("text"))
    return "\n".join(text_parts)


def _extract_with_pdfplumber(file_path: str) -> str:
    """Extraction avec pdfplumber."""
    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def _clean_text(text: str) -> str:
    """Nettoie le texte extrait : supprime les espaces multiples et les lignes vides."""
    import re
    # Supprimer les caractères non imprimables courants
    text = text.replace('\x00', '')
    # Réduire les espaces multiples
    text = re.sub(r'[ \t]+', ' ', text)
    # Réduire les sauts de ligne multiples
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def get_pdf_metadata(file_path: str) -> dict:
    """Récupère les métadonnées d'un fichier PDF (nombre de pages, etc.)."""
    meta = {"pages": 0, "size_bytes": 0}

    if os.path.exists(file_path):
        meta["size_bytes"] = os.path.getsize(file_path)

    if _HAS_FITZ:
        try:
            with fitz.open(file_path) as doc:
                meta["pages"] = doc.page_count
        except Exception:
            pass

    return meta
