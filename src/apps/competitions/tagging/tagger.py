import logging
import os
import re

from django.utils.html import strip_tags
from competitions.models import Competition, Tag, TagCategory
from .deberta_classifier import DebertaClassifier
from .regex_classifier import CONFERENCES, FIELDS_OF_APPLICATION, ML_DOMAINS, RegexClassifier
from .sklearn_classifier import SklearnClassifier

logger = logging.getLogger(__name__)

ALLOWED_PAGE_TITLES = {"overview", "description", "rules", "evaluation", "competition", "participation"}

DEFAULT_MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
TFIDF_MODEL_PATH = os.path.join(DEFAULT_MODELS_DIR, "tfidf_model.pkl")
DEBERTA_MODEL_PATH = os.path.join(DEFAULT_MODELS_DIR, "fields_deberta")


def get_default_classifiers():
    """Build mapping of TagCategory to its corresponding classifier."""
    # Fallback chain: DeBERTa -> TF-IDF (Sklearn) -> Regex keywords
    return {
        "Conferences": RegexClassifier(CONFERENCES),
        "Machine Learning Domain": SklearnClassifier.load(
            "Machine Learning Domain",
            model_path=TFIDF_MODEL_PATH,
            fallback=RegexClassifier(ML_DOMAINS),
        ),
        "Fields of Application": DebertaClassifier.load(
            model_path=DEBERTA_MODEL_PATH,
            fallback=SklearnClassifier.load(
                "Fields of Application",
                model_path=TFIDF_MODEL_PATH,
                fallback=RegexClassifier(FIELDS_OF_APPLICATION),
            ),
        ),
    }


def build_competition_text(comp):
    """Concatenate competition title, description, reward, and relevant pages."""
    parts = []

    if comp.title:
        title = strip_tags(comp.title).strip()
        if title:
            parts.append(title)

    if comp.description:
        desc = re.sub(r"\s+", " ", strip_tags(comp.description)).strip()
        if desc:
            parts.append(desc)

    if comp.reward:
        reward = re.sub(r"\s+", " ", strip_tags(str(comp.reward))).strip()
        if reward:
            parts.append(f"Reward: {reward}")

    # Only include informative competition pages
    for page in comp.pages.all():
        title_norm = re.sub(r"\.(md|txt)$", "", (page.title or "").lower()).strip()
        if any(allowed in title_norm for allowed in ALLOWED_PAGE_TITLES):
            if page.content:
                content = re.sub(r"\s+", " ", strip_tags(page.content)).strip()
                if content:
                    parts.append(content)

    return " : ".join(parts)


def tag_competition_text(text, classifiers=None):
    """Predict tags across configured classifiers for a given text."""
    if not text:
        return {}

    active_classifiers = classifiers if classifiers is not None else get_default_classifiers()
    results = {}
    for category, classifier in active_classifiers.items():
        try:
            tags = classifier.predict(text)
            if tags:
                results[category] = tags
        except Exception as e:
            logger.error("Classifier error for category '%s': %s", category, e)
    return results


def auto_tag_competition(competition_id, overwrite=False, classifiers=None):
    """Auto-tag a single competition. If overwrite is False, skips if competition has tags."""
    try:
        comp = Competition.objects.prefetch_related("pages", "tags").get(id=competition_id)
    except Competition.DoesNotExist:
        logger.warning("Competition %s does not exist for auto-tagging", competition_id)
        return []

    # Only tag if competition has no tags (unless overwrite is True)
    if comp.tags.exists() and not overwrite:
        logger.info("Competition %s already has tags, skipping auto-tagging", competition_id)
        return list(comp.tags.all())

    full_text = build_competition_text(comp)
    if not full_text.strip():
        logger.info("Competition %s has no text to tag", competition_id)
        return []

    predicted_tags = tag_competition_text(full_text, classifiers=classifiers)
    if not predicted_tags:
        logger.info("No tags predicted for competition %s", competition_id)
        return []

    # Match predictions against existing DB tags without creating new ones
    tags_to_add = []
    for cat_name, tag_names in predicted_tags.items():
        if not tag_names:
            continue

        cat_obj = TagCategory.objects.filter(name__iexact=cat_name).first()
        if not cat_obj:
            continue

        for tag_name in tag_names:
            tag_obj = Tag.objects.filter(category=cat_obj, name__iexact=tag_name).first()
            if not tag_obj:
                continue
            if tag_obj not in tags_to_add:
                tags_to_add.append(tag_obj)

    if tags_to_add:
        if overwrite:
            comp.tags.set(tags_to_add)
        else:
            comp.tags.add(*tags_to_add)
        logger.info(
            "Auto-tagged competition %s with %d tags: %s",
            competition_id,
            len(tags_to_add),
            [f"{t.category.name}: {t.name}" for t in tags_to_add],
        )

    return tags_to_add
