from abc import ABC, abstractmethod


class WitInterface(ABC):
    """
    Interface for the Wit Version Control System.
    Defines the required methods for any implementation.
    """

    @abstractmethod
    def init(self) -> str:
        """Initialize a new Wit repository."""
        pass

    @abstractmethod
    def add(self, path: str) -> str:
        """Add a file or directory to Staging."""
        pass

    @abstractmethod
    def commit(self, message: str) -> str:
        """Save a new version to the Repository."""
        pass

    @abstractmethod
    def status(self) -> str:
        """View the current file status."""
        pass

    @abstractmethod
    def checkout(self, commit_id: str) -> str:
        """Restore the project to a specific commit."""
        pass

    @abstractmethod
    def log(self) -> str:
        """View commit history."""
        pass

    @abstractmethod
    def add_to_ignore(self, filename: str) -> str:
        """Add a file to .witignore."""
        pass