from abc import ABC, abstractmethod

class BaseOperation(ABC):
    """Base class for all document processing operations."""

    @abstractmethod
    async def execute(self, context):
        """Execute the operation."""
        pass