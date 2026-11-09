"""
SmartRecruit IA — Extraction d'entités depuis le texte d'un CV.

Stratégie hybride :
  1. SpaCy (modèle fr_core_news_md ou en_core_web_sm) si disponible
  2. Regex + heuristiques en fallback (toujours disponible)

Entités extraites : nom, email, téléphone, compétences, formations,
expériences professionnelles, langues.
"""

import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# ── Tentative d'import SpaCy ────────────────────────────────────────────────────
try:
    import spacy
    _HAS_SPACY = True
except ImportError:
    _HAS_SPACY = False
    logger.info("SpaCy non disponible — utilisation du fallback regex.")

_NLP_MODEL = None


def _get_nlp_model():
    """Charge le modèle SpaCy une seule fois (optimisation mémoire)."""
    global _NLP_MODEL
    if _NLP_MODEL is not None:
        return _NLP_MODEL

    if not _HAS_SPACY:
        return None

    for model_name in ('fr_core_news_md', 'fr_core_news_sm', 'en_core_web_sm'):
        try:
            _NLP_MODEL = spacy.load(model_name)
            logger.info(f"Modèle SpaCy chargé : {model_name}")
            return _NLP_MODEL
        except OSError:
            continue
        except Exception as exc:
            logger.warning(f"Erreur chargement {model_name} : {exc}")
            continue

    logger.info("Aucun modèle SpaCy trouvé — utilisation du fallback regex uniquement.")
    return None


# ── Bases de référence pour la reconnaissance ───────────────────────────────────

# Compétences techniques courantes (non exhaustif, extensible)
SKILL_KEYWORDS = [
    # Langages
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "PHP", "Ruby",
    "Go", "Rust", "Kotlin", "Swift", "Scala", "R", "MATLAB", "Perl", "Shell", "Bash",
    # Frameworks
    "Django", "Flask", "FastAPI", "React", "Vue", "Angular", "Spring", "Laravel",
    "Express", "Next.js", "Nuxt", "Rails", "ASP.NET", "Bootstrap", "Tailwind",
    # Bases de données
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Oracle", "SQL Server",
    "SQLite", "Cassandra", "DynamoDB", "Firebase", "Supabase",
    # Cloud / DevOps
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD", "Jenkins", "GitLab CI",
    "GitHub Actions", "Terraform", "Ansible", "Nginx", "Linux", "Unix",
    # Data / IA
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Keras",
    "Scikit-learn", "Pandas", "NumPy", "Spark", "Hadoop", "Tableau", "Power BI",
    "NLP", "Computer Vision", "Data Science", "Big Data", "ETL",
    # Outils
    "Git", "Jira", "Confluence", "Slack", "Notion", "Figma", "Agile", "Scrum",
    "REST", "GraphQL", "gRPC", "Microservices", "Kafka", "RabbitMQ", "Celery",
    # Mobile
    "Android", "iOS", "Flutter", "React Native",
    # Autres
    "HTML", "CSS", "Sass", "Webpack", "Vite", "Vitest", "Jest", "pytest",
    "Selenium", "Cypress", "Cucumber", "TDD", "BDD",
]

# Sectionneaux de CV (pour découper le document en parties)
SECTION_PATTERNS = {
    'experience': [
        r'(?i)\b(exp[ée]rience(?:\s+professionnelle)?|professional\s+experience|work\s+experience|emplois?|stages?)\b',
    ],
    'education': [
        r'(?i)\b(formation|educations?|dipl[ôo]mes?|studies?|academics?)\b',
    ],
    'skills': [
        r'(?i)\b(comp[ée]tences?|skills?|technologies?|outils?|tools?|techniques)\b',
    ],
    'languages': [
        r'(?i)\b(langues?|languages?)\b',
    ],
    'projects': [
        r'(?i)\b(projets?|projects?|r[ée]alisations?)\b',
    ],
}

LANGUAGES_KNOWN = [
    "Français", "Anglais", "Espagnol", "Allemand", "Italien", "Arabe",
    "Chinois", "Japonais", "Portugais", "Russe", "Néerlandais", "Turc",
]


# ═══════════════════════════════════════════════════════════════════════════════
#  EXTRACTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

def extract_entities(text: str) -> Dict:
    """
    Extrait les entités structurées depuis le texte d'un CV.

    Returns:
        {
            "name": str,
            "email": str,
            "phone": str,
            "location": str,
            "skills": [str, ...],
            "education": [{institution, degree, year}, ...],
            "experience": [{company, position, duration, description}, ...],
            "languages": [str, ...],
            "summary": str,
        }
    """
    if not text or not text.strip():
        return _empty_result()

    result = {
        'name':       _extract_name(text),
        'email':      _extract_email(text),
        'phone':      _extract_phone(text),
        'location':   _extract_location(text),
        'skills':     _extract_skills(text),
        'education':  _extract_education(text),
        'experience': _extract_experience(text),
        'languages':  _extract_languages(text),
        'summary':    '',
    }

    # Enrichissement via SpaCy si disponible
    nlp = _get_nlp_model()
    if nlp:
        _enrich_with_spacy(nlp, text, result)

    # Génération d'un résumé court
    result['summary'] = _build_summary(result)

    return result


def _empty_result() -> Dict:
    return {
        'name': '', 'email': '', 'phone': '', 'location': '',
        'skills': [], 'education': [], 'experience': [],
        'languages': [], 'summary': '',
    }


# ── Extraction : Nom ─────────────────────────────────────────────────────────────

def _extract_name(text: str) -> str:
    """Tente d'extraire le nom du candidat depuis les premières lignes."""
    lines = [l.strip() for l in text.split('\n') if l.strip()][:10]

    # Le nom est généralement dans les 2-3 premières lignes
    for line in lines[:5]:
        # Ignorer les lignes contenant des emails ou téléphones
        if '@' in line or re.search(r'\d{4,}', line):
            continue
        # Le nom ressemble à 2-4 mots capitalisés
        words = line.split()
        if 2 <= len(words) <= 4:
            if all(w[0].isupper() or w[0].isalpha() for w in words):
                # Éviter les phrases avec des mots courants
                lower_words = {w.lower() for w in words}
                common = {'curriculum', 'vitae', 'resume', 'cv', 'profile', 'profil'}
                if not (lower_words & common):
                    return line

    # Fallback SpaCy pour les PER (entity detection)
    return lines[0] if lines else ''


# ── Extraction : Email ──────────────────────────────────────────────────────────

def _extract_email(text: str) -> str:
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0).lower() if match else ''


# ── Extraction : Téléphone ───────────────────────────────────────────────────────

def _extract_phone(text: str) -> str:
    patterns = [
        r'(?:\+216|00216)?[\s.-]?(?:2\d|5\d|7\d|9\d)[\s.-]?\d{3}[\s.-]?\d{3}',  # Tunisie
        r'\+33[\s.-]?\d(?:[\s.-]?\d){8}',                                        # France
        r'\+1[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',                        # USA
        r'(?:\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',            # Générique
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(0).strip()
            return phone
    return ''


# ── Extraction : Localisation ──────────────────────────────────────────────────

def _extract_location(text: str) -> str:
    cities = [
        'Tunis', 'Ariana', 'Ben Arous', 'Manouba', 'Nabeul', 'Bizerte',
        'Sousse', 'Monastir', 'Mahdia', 'Sfax', 'Kairouan', 'Kasserine',
        'Sidi Bouzid', 'Gabès', 'Médenine', 'Tataouine', 'Gafsa', 'Tozeur',
        'Kebili', 'Jendouba', 'Le Kef', 'Siliana', 'Beja', 'Zaghouan',
        'Paris', 'Lyon', 'Marseille', 'Toulouse', 'Bordeaux', 'Lille',
        'Nice', 'Nantes', 'Strasbourg', 'Rennes', 'Montpellier', 'Grenoble',
    ]
    for city in cities:
        if re.search(rf'\b{re.escape(city)}\b', text, re.IGNORECASE):
            return city
    return ''


# ── Extraction : Compétences ────────────────────────────────────────────────────

def _extract_skills(text: str) -> List[str]:
    """Détecte les compétences mentionnées dans le CV."""
    text_lower = text.lower()
    found = []

    for skill in SKILL_KEYWORDS:
        # Recherche insensible à la casse, mot entier
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            # Normaliser la casse (première lettre majuscule pour les acronymes courts)
            if len(skill) <= 3 or skill.isupper():
                found.append(skill)
            else:
                found.append(skill)

    # Déduplication en préservant l'ordre
    seen = set()
    unique = []
    for s in found:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return unique


# ── Extraction : Formations ──────────────────────────────────────────────────────

def _extract_education(text: str) -> List[Dict]:
    """Extrait les formations mentionnées."""
    education = []
    section = _extract_section(text, 'education')

    degrees = [
        ('Doctorat', 'Doctorat'),
        ('PhD', 'PhD'),
        ('Master', 'Master'),
        ('Mastère', 'Mastère'),
        ('Ingénieur', "Diplôme d'Ingénieur"),
        ('Engineering', "Diplôme d'Ingénieur"),
        ('Licence', 'Licence'),
        ('Bachelor', 'Bachelor'),
        ('BTS', 'BTS'),
        ('DUT', 'DUT'),
        ('DEUG', 'DEUG'),
        ('Baccalauréat', 'Baccalauréat'),
        ('Bac ', 'Baccalauréat'),
        ('MBA', 'MBA'),
        ('DESS', 'DESS'),
        ('DEA', 'DEA'),
    ]

    search_text = section if section else text
    years = re.findall(r'(19|20)\d{2}', search_text)

    for keyword, degree_label in degrees:
        if keyword.lower() in search_text.lower():
            education.append({
                'degree': degree_label,
                'institution': '',
                'year': '',
            })
            if len(education) >= 5:
                break

    # Si aucune formation détectée mais on a des années
    if not education and years:
        education.append({
            'degree': '',
            'institution': '',
            'year': years[0],
        })

    return education


# ── Extraction : Expériences ────────────────────────────────────────────────────

def _extract_experience(text: str) -> List[Dict]:
    """Extrait les expériences professionnelles."""
    experiences = []
    section = _extract_section(text, 'experience')
    search_text = section if section else text
    lines = [l.strip() for l in search_text.split('\n') if l.strip()]

    # Patterns de date/durée
    date_pattern = re.compile(
        r'((?:19|20)\d{2}|janv|f[ée]v|mars|avr|mai|juin|juil|ao[ûu]t|sept|oct|nov|d[ée]c|'
        r'jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec|'
        r'\d{2}/\d{2,4}|pr[ée]sent|now|actuel)', re.IGNORECASE
    )

    current_exp = None
    for line in lines:
        if date_pattern.search(line):
            if current_exp and (current_exp.get('position') or current_exp.get('company')):
                experiences.append(current_exp)
            current_exp = {
                'company': '',
                'position': '',
                'duration': line.strip(),
                'description': '',
            }
        elif current_exp is not None:
            if not current_exp['position']:
                current_exp['position'] = line[:100]
            elif not current_exp['company']:
                current_exp['company'] = line[:100]
            else:
                current_exp['description'] = (current_exp['description'] + ' ' + line)[:200].strip()
        else:
            # Heuristique : ligne sans date potentiellement un titre de poste
            # On crée quand même une entrée pour ne pas perdre l'info
            current_exp = {
                'company': '',
                'position': line[:100],
                'duration': '',
                'description': '',
            }

    if current_exp and (current_exp.get('position') or current_exp.get('company')):
        experiences.append(current_exp)

    # Fallback : chercher des patterns "Poste chez Entreprise" dans tout le texte
    if not experiences:
        chez_pattern = re.compile(
            r'([A-ZÀ-Ü][^.]{5,50})\s+(?:chez|at|@|,)\s+([A-ZÀ-Ü][^.\n]{3,50})',
            re.IGNORECASE
        )
        for match in chez_pattern.finditer(text):
            experiences.append({
                'company': match.group(2).strip()[:100],
                'position': match.group(1).strip()[:100],
                'duration': '',
                'description': '',
            })
            if len(experiences) >= 5:
                break

    return experiences[:10]


# ── Extraction : Langues ──────────────────────────────────────────────────────────

def _extract_languages(text: str) -> List[str]:
    found = []
    for lang in LANGUAGES_KNOWN:
        if re.search(rf'\b{re.escape(lang)}\b', text, re.IGNORECASE):
            found.append(lang)
    return found


# ── Découpage par section ──────────────────────────────────────────────────────────

def _extract_section(text: str, section_name: str) -> str:
    """Extrait le texte d'une section spécifique du CV."""
    patterns = SECTION_PATTERNS.get(section_name, [])
    if not patterns:
        return ''

    text_lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            start = match.start()
            # Trouver la prochaine section
            end = len(text)
            for other_section, other_patterns in SECTION_PATTERNS.items():
                if other_section == section_name:
                    continue
                for other_pattern in other_patterns:
                    other_match = re.search(other_pattern, text[start + 1:])
                    if other_match:
                        candidate_end = start + 1 + other_match.start()
                        if candidate_end < end:
                            end = candidate_end
            return text[start:end].strip()

    return ''


# ── Enrichissement SpaCy ──────────────────────────────────────────────────────────

def _enrich_with_spacy(nlp, text: str, result: Dict):
    """Utilise SpaCy pour enrichir les entités extraites."""
    try:
        doc = nlp(text[:100000])  # Limiter la taille pour la performance
    except Exception as exc:
        logger.warning(f"Erreur SpaCy : {exc}")
        return

    # Extraire les personnes (PER) si le nom est vide
    if not result['name']:
        for ent in doc.ents:
            if ent.label_ == 'PER':
                result['name'] = ent.text.strip()
                break

    # Extraire les organisations (ORG) dans les expériences
    if not result['experience']:
        orgs = [ent.text.strip() for ent in doc.ents if ent.label_ == 'ORG']
        for org in orgs[:5]:
            result['experience'].append({
                'company': org,
                'position': '',
                'duration': '',
                'description': '',
            })

    # Extraire les lieux (GPE/LOC)
    if not result['location']:
        for ent in doc.ents:
            if ent.label_ in ('GPE', 'LOC'):
                result['location'] = ent.text.strip()
                break


# ── Construction du résumé ──────────────────────────────────────────────────────

def _build_summary(result: Dict) -> str:
    """Construit un résumé textuel court du profil."""
    parts = []

    if result['name']:
        parts.append(f"Candidat : {result['name']}")

    if result['skills']:
        parts.append(f"Compétences : {', '.join(result['skills'][:10])}")

    if result['experience']:
        parts.append(f"Expériences : {len(result['experience'])} poste(s)")

    if result['education']:
        degrees = [e['degree'] for e in result['education'] if e.get('degree')]
        if degrees:
            parts.append(f"Formation : {', '.join(degrees)}")

    if result['languages']:
        parts.append(f"Langues : {', '.join(result['languages'])}")

    return ' | '.join(parts) if parts else ''
