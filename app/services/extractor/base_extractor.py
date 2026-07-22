from abc import ABC, abstractmethod


class BaseExtractor(ABC):

    @abstractmethod
    def extract(self, buyer, html):
        """
        Extract data from HTML
        and update Buyer object.
        """
        pass