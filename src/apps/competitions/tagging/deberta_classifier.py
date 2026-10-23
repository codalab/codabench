import logging
import os

from .base_classifier import BaseTagClassifier

logger = logging.getLogger(__name__)


class DebertaClassifier(BaseTagClassifier):
    """Tag classifier using a fine-tuned DeBERTa / Transformer model."""

    def __init__(self, model, tokenizer, labels, device="cpu", threshold=0.5, max_length=512):
        self.model = model
        self.tokenizer = tokenizer
        self.labels = labels
        self.device = device
        self.threshold = threshold
        self.max_length = max_length

    @classmethod
    def load(cls, model_path, fallback=None, threshold=0.5, max_length=512):
        """Load a fine-tuned DeBERTa model from a Hugging Face checkpoint directory."""
        if not os.path.exists(model_path):
            return fallback

        try:
            # Lazy import torch/transformers to keep dependencies optional
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            device = "cuda" if torch.cuda.is_available() else "cpu"
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForSequenceClassification.from_pretrained(model_path)
            model.to(device)
            model.eval()
            labels = [model.config.id2label[i] for i in sorted(model.config.id2label.keys())]
            return cls(
                model=model,
                tokenizer=tokenizer,
                labels=labels,
                device=device,
                threshold=threshold,
                max_length=max_length,
            )
        except ImportError:
            logger.info("torch/transformers not installed; using fallback for DeBERTa classifier")
            return fallback
        except Exception as exc:
            logger.warning("Failed to load DeBERTa model from '%s': %s", model_path, exc)
            return fallback

    def predict(self, text):
        if not text or not text.strip():
            return []

        import torch
        inputs = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        ).to(self.device)
        # Multi-label prediction with sigmoid activation
        with torch.no_grad():
            probs = torch.sigmoid(self.model(**inputs).logits).squeeze(0).cpu().numpy()
        return [label for label, p in zip(self.labels, probs) if p >= self.threshold]
