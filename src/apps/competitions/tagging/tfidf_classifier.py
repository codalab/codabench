import json

import numpy as np
import onnxruntime as ort

from .base_classifier import BaseTagClassifier


class TfidfClassifier(BaseTagClassifier):
    """Multi-label TF-IDF classifier running an ONNX pipeline via onnxruntime.

    Expects an ONNX model exported from a scikit-learn text pipeline with:
    - input[0]: string tensor of shape (batch, 1)
    - output[1]: probability tensor of shape (batch, num_labels) (zipmap=False)
    - metadata key "codabench_tagging": JSON {"labels": [...], "thresholds": [...], "fallback_tag": "..."}
    """

    def __init__(self, model_path):
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 1
        opts.inter_op_num_threads = 1
        self.session = ort.InferenceSession(model_path, sess_options=opts, providers=["CPUExecutionProvider"])

        meta = json.loads(self.session.get_modelmeta().custom_metadata_map["codabench_tagging"])
        self._labels = list(meta["labels"])
        self.thresholds = list(meta["thresholds"])
        self.fallback_tag = meta.get("fallback_tag") or None

        self.input_name = self.session.get_inputs()[0].name
        self.prob_output_name = self.session.get_outputs()[1].name

    @property
    def labels(self):
        return self._labels

    def predict(self, text):
        fallback = [self.fallback_tag] if self.fallback_tag else []
        if not text or not text.strip():
            return fallback

        probs = self.session.run([self.prob_output_name], {self.input_name: np.array([[text.lower()]])})[0][0]
        predicted = [
            tag
            for tag, prob, threshold in zip(self._labels, probs, self.thresholds)
            if prob >= threshold
        ]
        return predicted or fallback
