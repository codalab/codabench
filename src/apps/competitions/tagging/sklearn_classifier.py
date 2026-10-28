import logging
import os
import pickle

from competitions.default_tags import DEFAULT_TAXONOMY
from .base_classifier import BaseTagClassifier

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "tfidf_model.pkl")


class SklearnClassifier(BaseTagClassifier):
    """TF-IDF + Logistic Regression classifier for a tag category."""

    def __init__(self, vectorizer, classifiers, labels, threshold=0.5):
        self.vectorizer = vectorizer
        self.classifiers = classifiers
        self.labels = labels
        self.threshold = threshold

    @classmethod
    def load(cls, category, model_path=None, fallback=None, threshold=0.5):
        """Load category classifiers from a serialized TF-IDF model bundle."""
        path = model_path or DEFAULT_MODEL_PATH
        if not os.path.exists(path):
            return fallback

        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
        except Exception as e:
            logger.warning("Failed to load model '%s': %s", path, e)
            return fallback

        if category not in data:
            return fallback

        m = data[category]
        labels = DEFAULT_TAXONOMY.get(category, [])
        # Ensure model classifier count matches the taxonomy tags
        if len(labels) != len(m.get("classifiers", [])):
            logger.warning("Classifier count mismatch for '%s', using fallback", category)
            return fallback

        return cls(
            vectorizer=m["vectorizer"],
            classifiers=m["classifiers"],
            labels=labels,
            threshold=threshold,
        )

    def predict(self, text):
        if not text or not text.strip():
            return []

        Z = self.vectorizer.transform([text])
        # Run OvR binary classifiers and select tags above probability threshold
        return [
            self.labels[j]
            for j, clf in enumerate(self.classifiers)
            if clf is not None and clf.predict_proba(Z)[0, 1] >= self.threshold
        ]
