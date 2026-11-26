from collections import defaultdict
from functools import lru_cache
import os

from competitions.models import Tag

from .regex_classifier import RegexClassifier
from .tfidf_classifier import TfidfClassifier
from .utils import build_competition_text

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

CONFERENCE = {
    "NeurIPS": [r"\bneurips\b", r"\bnips\b"],
    "CVPR": [r"\bcvpr\b"],
    "ICML": [r"\bicml\b"],
    "ICLR": [r"\biclr\b"],
    "ICCV": [r"\biccv\b"],
    "ECCV": [r"\beccv\b"],
    "ACL": [r"\bacl\b"],
    "MICCAI": [r"\bmiccai\b"],
    "NAACL": [r"\bnaacl\b"],
    "WSDM": [r"\bwsdm\b"],
    "ECML PKDD": [r"\becml\b", r"\bpkdd\b"],
    "SemEval": [r"\bsemeval\b"],
}


@lru_cache(maxsize=1)
def get_classifiers():
    """Map each tag category to its classifier."""
    return {
        "Machine Learning Domain": TfidfClassifier(os.path.join(MODELS_DIR, "tfidf", "ml_domain.onnx")),
        "Fields of Application": TfidfClassifier(os.path.join(MODELS_DIR, "tfidf", "field.onnx")),
        "Conference": RegexClassifier(CONFERENCE),
    }


def suggest_tags_for_competition(competition=None, title="", description="", pages=None):
    """Return suggested Tag IDs matching the competition text across all DB categories."""
    text = build_competition_text(competition=competition, title=title, description=description, pages=pages)
    if not text.strip():
        return []

    tags_by_category = defaultdict(list)
    for tag in Tag.objects.select_related("category").all():
        tags_by_category[tag.category.name].append(tag)

    classifiers = get_classifiers()
    matched_ids = []

    for cat_name, db_tags in tags_by_category.items():
        classifier = classifiers.get(cat_name)
        predicted = {name.lower() for name in classifier.predict(text)} if classifier else set()
        covered = {name.lower() for name in classifier.labels} if classifier else set()
        fallback = classifier.fallback_tag.lower() if classifier and classifier.fallback_tag else None

        uncovered_tags = [tag.name for tag in db_tags if tag.name.lower() not in covered and tag.name.lower() != fallback]
        uncovered_pred = {name.lower() for name in RegexClassifier(uncovered_tags).predict(text)}

        chosen_tags = (predicted - {fallback}) | uncovered_pred or (predicted & {fallback})
        matched_ids.extend(tag.id for tag in db_tags if tag.name.lower() in chosen_tags)

    return matched_ids
