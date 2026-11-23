import re

from .base_classifier import BaseTagClassifier


class RegexClassifier(BaseTagClassifier):
    """Multi-label classifier matching tags against regex rules (dict) or exact tag names (iterable)."""

    def __init__(self, rules, fallback_tag=None):
        if not isinstance(rules, dict):
            rules = {name: [rf"(?<!\w){re.escape(name.strip())}(?!\w)"] for name in rules if name.strip()}

        self.compiled_rules = {
            tag: re.compile("|".join(patterns), re.IGNORECASE)
            for tag, patterns in rules.items()
        }
        self.fallback_tag = fallback_tag

    @property
    def labels(self):
        return self.compiled_rules.keys()

    def predict(self, text):
        fallback = [self.fallback_tag] if self.fallback_tag else []
        if not text:
            return fallback
        matched = [
            tag
            for tag, pattern in self.compiled_rules.items()
            if pattern.search(text)
        ]
        return matched or fallback
