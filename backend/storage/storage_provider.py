from abc import ABC, abstractmethod
from fastapi import UploadFile

class StorageProvider(ABC):
    @abstractmethod
    async def save(self, file: UploadFile, filename: str, folder: str = "media") -> str:
        """Saves a file and returns its public URL/path."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Deletes a file given its storage key."""
        pass

    @abstractmethod
    def get_url(self, key: str) -> str:
        """Returns the public URL/path for a storage key."""
        pass
