import abc

class BaseTagClassifier(abc.ABC):
    @abc.abstractmethod
    def predict(self, text):
        pass
