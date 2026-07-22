from abc import ABC, abstractmethod


class BaseSearchAdapter(ABC):
    """
    Base class for every search source.
    """

    def __init__(self):

        self.max_results = 20

    @abstractmethod
    def search(self, keyword):
        """
        Returns raw search results.
        """
        pass