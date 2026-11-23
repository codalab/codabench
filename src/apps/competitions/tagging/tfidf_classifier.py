from collections import Counter
import math
import pickle
import re

from .base_classifier import BaseTagClassifier

_TOKEN_RE = re.compile(r"(?u)\b\w\w+\b")


class TfidfClassifier(BaseTagClassifier):
    """Pure-Python (1, 2)-gram sublinear TF-IDF + logistic regression classifier."""

    def __init__(self, category_model):
        self.vocabulary = category_model["vocabulary"]
        self.idf = category_model["idf"]
        self.classifiers = category_model["classifiers"]
        self.fallback_tag = category_model.get("fallback_tag") or None

    @property
    def labels(self):
        return self.classifiers.keys()

    @classmethod
    def load_all(cls, path):
        """Load all category classifiers from a pickled model bundle."""
        with open(path, "rb") as f:
            bundle = pickle.load(f)
        return {cat_name: cls(cat_model) for cat_name, cat_model in bundle.items()}

    def _vectorize(self, text):
        # Compute L2-normalized sublinear TF-IDF vector over unigrams and bigrams
        tokens = _TOKEN_RE.findall(text.lower())
        ngrams = tokens + [f"{a} {b}" for a, b in zip(tokens, tokens[1:])]
        counts = Counter(ng for ng in ngrams if ng in self.vocabulary)
        sparse = {
            self.vocabulary[ng]: (1.0 + math.log(tf)) * self.idf[self.vocabulary[ng]]
            for ng, tf in counts.items()
        }
        norm = math.hypot(*sparse.values())
        return {i: v / norm for i, v in sparse.items()} if norm else {}

    def predict(self, text):
        fallback = [self.fallback_tag] if self.fallback_tag else []
        sparse = self._vectorize(text or "")
        if not sparse:
            return fallback

        predicted = []
        for tag_name, clf in self.classifiers.items():
            logit = sum(clf["weights"].get(i, 0.0) * v for i, v in sparse.items()) + clf["intercept"]
            if 1.0 / (1.0 + math.exp(-max(-50.0, min(50.0, logit)))) >= clf["threshold"]:
                predicted.append(tag_name)
        return predicted or fallback
