from collections import Counter
import math
import os
import pickle
import re

from .base_classifier import BaseTagClassifier

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "tfidf_model.pkl")
_TOKEN_RE = re.compile(r"(?u)\b\w\w+\b")
_MODEL_CACHE = None


def _load_bundle(path=MODEL_PATH):
    global _MODEL_CACHE
    if path == MODEL_PATH and _MODEL_CACHE is not None:
        return _MODEL_CACHE
    with open(path, "rb") as f:
        bundle = pickle.load(f)
    if path == MODEL_PATH:
        _MODEL_CACHE = bundle
    return bundle


class TfidfClassifier(BaseTagClassifier):
    def __init__(self, category_model):
        self.vocabulary = category_model["vocabulary"]
        self.idf = category_model["idf"]
        self.ngram_range = tuple(category_model.get("ngram_range", (1, 2)))
        self.classifiers = category_model["classifiers"]

    @classmethod
    def load(cls, category_name, path=MODEL_PATH):
        bundle = _load_bundle(path)
        if category_name not in bundle:
            raise KeyError(f"Category '{category_name}' not found in {path}")
        return cls(bundle[category_name])

    def _vectorize(self, text):
        tokens = _TOKEN_RE.findall(text.lower())
        if not tokens:
            return {}

        ngrams = list(tokens)
        if self.ngram_range == (1, 2) and len(tokens) > 1:
            ngrams.extend(f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1))

        vocab = self.vocabulary
        counts = Counter(ng for ng in ngrams if ng in vocab)
        if not counts:
            return {}

        idf = self.idf
        sparse = {
            vocab[ng]: (1.0 + math.log(count)) * idf[vocab[ng]]
            for ng, count in counts.items()
        }

        norm = math.sqrt(sum(v * v for v in sparse.values()))
        if norm > 0.0:
            sparse = {idx: v / norm for idx, v in sparse.items()}

        return sparse

    def predict(self, text):
        if not text or not text.strip():
            return []

        sparse = self._vectorize(text)
        if not sparse:
            return []

        predicted = []
        for tag_name, clf in self.classifiers.items():
            w = clf["weights"]
            logit = sum(w.get(idx, 0.0) * val for idx, val in sparse.items()) + clf["intercept"]
            prob = 1.0 / (1.0 + math.exp(-max(-50.0, min(50.0, logit))))
            if prob >= clf["threshold"]:
                predicted.append(tag_name)

        return predicted
