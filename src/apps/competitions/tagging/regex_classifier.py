import re
from .base_classifier import BaseTagClassifier

ML_DOMAINS = {
    "Computer Vision": [
        r"\bvision\b", r"\bimages?\b", r"segmentation", r"object detection",
        r"image detection", r"visual detection", r"\bvideo\b", r"\bcv\b",
        r"\bpixels?\b", r"3d reconstruction",
    ],
    "NLP": [
        r"\bnlp\b", r"language", r"\btext\b", r"sentiment", r"translation",
        r"named entity", r"\bner\b", r"summari[sz]ation", r"question answer",
        r"\bqa\b", r"document", r"chatbot", r"dialog",
    ],
    "Tabular": [
        r"tabular", r"regression", r"feature engineering", r"\bxgboost\b",
        r"\blightgbm\b", r"\bcatboost\b", r"\brandom forest\b", r"\btables?\b",
        r"\bspreadsheets?\b",
    ],
    "Time Series": [
        r"time[ -]series", r"forecast", r"\banomaly\b", r"temporal",
    ],
    "LLM": [
        r"\bllm\b", r"large language", r"chatgpt", r"gpt-?[34o]?", r"llama",
        r"claude", r"prompt engineering", r"instruction tuning",
    ],
    "Generative AI": [
        r"generative", r"diffusion", r"\bgan\b", r"text-to-image",
        r"synthesis", r"autoencoder", r"\bvae\b",
    ],
    "Reinforcement Learning": [
        r"reinforcement", r"\bagent\b", r"\bpolicy\b", r"reward", r"\brl\b",
        r"\bq-learning\b",
    ],
    "Audio": [
        r"speech", r"\baudio\b", r"\bsound\b", r"\bvoice\b", r"acoustic",
        r"music", r"speaker", r"\bwav\b",
    ],
    "Graphs": [
        r"\bgraphs?\b", r"\bnode\b", r"knowledge graph", r"link prediction",
        r"graph neural network", r"\bgnn\b",
    ],
    "Multimodal": [
        r"\bmultimodal\b", r"multi-modal", r"vision-language", r"cross-modal",
        r"\bvqa\b",
    ],
    "AutoML": [
        r"\bautoml\b", r"\bnas\b", r"hyperparameter", r"\bhpo\b",
        r"\bmodel tuning\b", r"\bhyperparameter tuning\b", r"\boptuna\b",
    ],
    "Algorithms": [
        r"\balgorithm\b", r"\bsearch\b", r"optimization", r"heuristic",
        r"\bsort(?:ing)?\b",
    ],
}

FIELDS_OF_APPLICATION = {
    "Healthcare": [
        r"health", r"medic", r"clinical", r"tumor", r"cancer", r"disease",
        r"patient", r"hospital", r"radiolog", r"diagnos", r"drug", r"covid",
        r"patholog", r"\bmri\b", r"\bct scan", r"\bcomputed tomography\b",
    ],
    "Biology": [
        r"\bbiolog", r"\bbiomedic", r"\bbiotech", r"\bbioinformatics\b",
        r"\bgenes?\b", r"\bgenetic", r"protein", r"\bcells?\b", r"\bcellular\b",
        r"\bgenomics?\b", r"\bmolecular\b", r"\bdna\b", r"\brna\b",
    ],
    "Finance": [
        r"financ", r"\bstock\b", r"\bmarket\b", r"trading",
        r"fraud", r"insurance", r"\bbank",
    ],
    "E-commerce": [
        r"e-commerce", r"ecommerce", r"\bretail\b", r"\bproducts?\b",
        r"\bshops?\b", r"\bshopping\b", r"customer", r"\bsales\b",
    ],
    "Earth Observation": [
        r"satellite", r"remote sensing", r"earth observation", r"sentinel",
        r"landsat",
    ],
    "Climate": [
        r"climate", r"weather", r"meteorolog", r"carbon", r"emission",
    ],
    "Energy": [
        r"\benergy\b", r"\bsolar\b", r"\bwind\b", r"renewable",
        r"power grid", r"electricity",
    ],
    "Robotics": [
        r"robot", r"autonomous", r"\bdriving\b", r"\bvehicle\b",
        r"navigation", r"\bdrone\b", r"manipulation",
    ],
    "Cybersecurity": [
        r"cyber", r"security", r"\bprivacy\b", r"adversarial attack",
        r"malware", r"\battack\b", r"\bdefen[sc]e", r"intrusion",
    ],
    "Transportation": [
        r"traffic", r"transport", r"mobility", r"\broutes?\b",
        r"logistics", r"transit",
    ],
    "Agriculture": [
        r"agricultur", r"\bcrop\b", r"\bplant\b", r"\bfood\b", r"farm",
    ],
    "Sports": [
        r"sport", r"football", r"soccer", r"basketball", r"athlete",
    ],
    "Education": [
        r"education", r"school", r"student", r"learning analytics", r"teaching",
    ],
    "Social Media": [
        r"social media", r"twitter", r"\bx\.com\b", r"facebook",
        r"instagram", r"reddit",
    ],
    "Astronomy": [
        r"astronomy", r"astrophysic", r"telescope", r"space", r"galaxy", r"cosmo",
    ],
    "Legal": [
        r"legal", r"\blaw\b", r"court", r"judicial", r"contract", r"statute",
    ],
    "Science": [
        r"physics", r"math", r"chemistry", r"scientific", r"quantum",
    ],
}

CONFERENCES = {
    "NeurIPS": [r"neurips", r"\bnips\b"],
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
}


class RegexClassifier(BaseTagClassifier):
    """Regex-based multi-label classifier matching keywords on text."""

    def __init__(self, rules):
        self.compiled = {
            tag: re.compile(r"|".join(pats), re.IGNORECASE)
            for tag, pats in rules.items()
        }

    def predict(self, text):
        if not text:
            return []
        return [tag for tag, rx in self.compiled.items() if rx.search(text)]
