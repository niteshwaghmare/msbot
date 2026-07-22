from services.ocr_service import OCRService
from services.validation_service import ValidationService
from services.siret_service import SiretService
from services.tin_service import TinService
from services.bank_service import BankService
from services.gst_service import GSTService

class OperationFactory:

    _operations = {
        "OCR": OCRService(),
        "VALIDATION": ValidationService(),
        "SIRET": SiretService(),
        "TIN": TinService(),
        "BANK": BankService(),
        "GST": GSTService(),
    }

    @classmethod
    def get(cls, operation_name):
        return cls._operations[operation_name]