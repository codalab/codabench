import abc


class BaseTagClassifier(abc.ABC):
    """Abstract base class for all tag category classifiers."""

    @abc.abstractmethod
    def predict(self, text):
        """Predict matched tag names for a given text string."""
        pass
