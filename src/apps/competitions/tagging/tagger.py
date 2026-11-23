from django.utils.html import strip_tags

from .regex_classifier import CONFERENCE, RegexClassifier
from .tfidf_classifier import TfidfClassifier

ALLOWED_PAGE_TITLES = {
    "overview",
    "description",
    "rules",
    "evaluation",
    "competition",
    "participation",
}

MAX_TEXT_LENGTH = 100_000
_CLASSIFIERS_CACHE = None


def get_default_classifiers():
    global _CLASSIFIERS_CACHE
    if _CLASSIFIERS_CACHE is None:
        _CLASSIFIERS_CACHE = {
            "Conference": RegexClassifier(CONFERENCE),
            "Machine Learning Domain": TfidfClassifier.load("Machine Learning Domain"),
            "Fields of Application": TfidfClassifier.load("Fields of Application"),
        }
    return _CLASSIFIERS_CACHE


def build_competition_text(competition=None, title="", description="", pages=None):
    if competition is not None:
        title = title or (competition.title or "")
        description = description or (competition.description or "")
        if pages is None:
            pages = list(competition.pages.all())

    parts = []
    if title:
        parts.append(str(title))
    if description:
        parts.append(str(description))

    if pages:
        for page in pages:
            if isinstance(page, dict):
                page_title = str(page.get("title") or "").strip().lower()
                page_content = page.get("content") or ""
            else:
                page_title = str(getattr(page, "title", "") or "").strip().lower()
                page_content = getattr(page, "content", "") or ""
            if page_title in ALLOWED_PAGE_TITLES and page_content:
                parts.append(str(page_content))

    raw_text = "\n".join(parts)[:MAX_TEXT_LENGTH]
    return strip_tags(raw_text)


def suggest_tags_for_competition(competition=None, title="", description="", pages=None):
    text = build_competition_text(
        competition=competition,
        title=title,
        description=description,
        pages=pages,
    )
    if not text.strip():
        return []

    classifiers = get_default_classifiers()
    predicted_pairs = {
        (category_name.lower(), tag_name.lower())
        for category_name, classifier in classifiers.items()
        for tag_name in classifier.predict(text)
    }
    if not predicted_pairs:
        return []

    from competitions.models import Tag

    return [
        tag.id
        for tag in Tag.objects.select_related("category").all()
        if (tag.category.name.lower(), tag.name.lower()) in predicted_pairs
    ]
