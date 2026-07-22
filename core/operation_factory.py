"""Factory for resolving configured workflow operations to services."""

from __future__ import annotations

from core.base_operations import BaseOperation
from services.bank_service import BankService
from services.duplicate_check import DuplicateCheckService
from services.gst_service import GSTService
from services.ocr_service import OCRService
from services.siret_service import SIRETService
from services.tin_service import TINService
from services.validation_service import ValidationService
from services.vendor_service import VendorService


class OperationFactory:
    """Returns operation services by their configuration key."""

    _operations: dict[str, BaseOperation] = {
        "OCR": OCRService(),
        "VALIDATION": ValidationService(),
        "SIRET": SIRETService(),
        "TIN": TINService(),
        "BANK": BankService(),
        "GST": GSTService(),
        "CREATE_VENDOR": VendorService(),
        "DUPLICATE_CHECK": DuplicateCheckService(),
    }

    @classmethod
    def get(cls, operation_name: str) -> BaseOperation:
        """Return the service registered for a configured operation name."""
        try:
            return cls._operations[operation_name]
        except KeyError as error:
            raise ValueError(f"Unknown operation: {operation_name}") from error
