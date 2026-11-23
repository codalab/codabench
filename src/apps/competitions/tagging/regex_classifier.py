import re
from .base_classifier import BaseTagClassifier

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


class RegexClassifier(BaseTagClassifier):
    def __init__(self, rules):
        self.compiled_rules = {
            tag: re.compile("|".join(patterns), re.IGNORECASE)
            for tag, patterns in rules.items()
        }

    def predict(self, text):
        if not text:
            return []
        return [
            tag
            for tag, pattern in self.compiled_rules.items()
            if pattern.search(text)
        ]
