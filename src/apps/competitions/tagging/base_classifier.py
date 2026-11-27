import abc


class BaseTagClassifier(abc.ABC):
    """Interface for per-category tag classifiers."""

    fallback_tag = None

    @property
    @abc.abstractmethod
    def labels(self):
        """Return tag names handled by this classifier (excluded from fallback keyword matching)."""
        pass

    @abc.abstractmethod
    def predict(self, text):
        """Return predicted tag names for the given competition text."""
        pass
