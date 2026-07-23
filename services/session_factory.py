"""

This module is responsible for creating, restoring, resetting, and normalizing
Vendor Onboarding session objects.

The session design is dynamic and country/document driven. Instead of storing
country-specific fields such as kbis_path, rib_path, w9_path, or bank_proof_path,
the session stores documents using a generic structure:

    session["documents"][document_type]

This allows the application to support multiple countries without changing the
session service whenever document requirements change.

Example:
    For France:
        documents = {
            "KIBS": {...},
            "RIB": {...}
        }

    For United States:
        documents = {
            "W9": {...},
            "BANK_PROOF": {...},
            "VENDOR_FORM": {...}
        }

Responsibilities:
    - Create empty default sessions.
    - Create country-specific sessions based on country configuration.
    - Build dynamic document state from country configuration.
    - Restore existing Redis sessions using the latest default schema.
    - Preserve requester and conversation context during reset.
    - Remove volatile bot fields before persistence.

This module does not read or write Redis directly.
Persistence is handled by session_service.py.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any


DEFAULT_SESSION: dict[str, Any] = {
    "request_id": None,
    "request_status": None,

    "country": None,
    "country_name": None,
    "currency": None,

    "user_language": "en",
    "language_confirmed": False,

    "conversation_initialized": False,
    "welcome_sent": False,

    "requester": {
        "llid": None,
        "email": None,
        "name": None,
    },

    "vendor": {
        "name": None,
        "city": None,
        "country": None,
        "tax_id": None,
        "vendor_id": None,
        "department": None,
        "industry": None,
        "supplier_group": [],
        "purchase_orgs": [],
        "selected_porg": None,
        "update_type": None,
    },

    "documents": {},

    "workflow": {
        "stage": None,
        "current_step": None,
        "completed_steps": [],
        "run_ocr": True,
        "run_document_validation": True,
        "run_bank_validation": False,
        "save_vendor_to_database": True,
    },

    "validation": {
        "existence_check_result": None,
        "duplicate_result": None,
        "document_validation_result": None,
        "bank_validation_result": None,
        "manual_review_required": False,
        "manual_review_reasons": [],
    },

    "files": {
        "pending_file": None,
    },

    "chat_history": [],

    # Volatile bot fields - not persisted
    "last_activity_id": None,
    "last_card": None,
}


PRESERVED_ON_RESET_FIELDS = {
    "requester",
    "user_language",
    "language_confirmed",
    "conversation_initialized",
    "welcome_sent",
}


VOLATILE_SESSION_FIELDS = {
    "last_activity_id",
    "last_card",
}


class SessionFactory:

    """
    Factory for creating and transforming Vendor Onboarding session state.

    SessionFactory centralizes all session structure rules so that the
    session_service remains focused only on persistence and orchestration.

    The factory supports:
        - Empty session creation.
        - Country-specific session creation.
        - Dynamic document-state generation.
        - Session restoration from Redis.
        - Reset session generation.
        - Volatile field cleanup before persistence.

    The session structure is intentionally generic and document-driven to
    support multiple countries and changing onboarding requirements.

    Design principle:
        Country-specific differences should come from configuration, not from
        hardcoded session fields.

    Example:
        session = SessionFactory.create_country_session(
            country_code="FR",
            country_config=fr_config,
            existing_session=current_session,
        )
    """


    @staticmethod
    def create_empty_session() -> dict[str, Any]:
        return deepcopy(DEFAULT_SESSION)

    @staticmethod
    def create_country_session(
        country_code: str,
        country_config: dict[str, Any],
        existing_session: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new session for selected country using country config.

        Example:
            FR config creates documents: KIBS, RIB
            US config creates documents: W9, BANK_PROOF, VENDOR_FORM
        """
        session = SessionFactory.create_empty_session()

        if existing_session:
            SessionFactory._preserve_common_fields(
                source=existing_session,
                target=session,
            )

        session["country"] = country_code
        session["country_name"] = country_config.get("countryName")
        session["currency"] = country_config.get("currency")
        session["user_language"] = country_config.get(
            "defaultLanguage",
            session.get("user_language", "en"),
        )

        session["vendor"]["country"] = country_code

        session["documents"] = SessionFactory._build_document_state(
            country_config=country_config,
        )

        workflow_config = country_config.get("workflow", {})

        session["workflow"]["run_ocr"] = workflow_config.get("runOcr", True)
        session["workflow"]["run_document_validation"] = workflow_config.get(
            "runDocumentValidation",
            True,
        )
        session["workflow"]["run_bank_validation"] = workflow_config.get(
            "runBankValidation",
            False,
        )
        session["workflow"]["save_vendor_to_database"] = workflow_config.get(
            "saveVendorToDatabase",
            True,
        )

        session["workflow"]["stage"] = "country_selected"
        session["workflow"]["current_step"] = SessionFactory._get_first_required_document(
            session["documents"]
        )

        return session

    @staticmethod
    def restore_session(
        data: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Restore session from Redis.

        Important:
        If new fields are added in DEFAULT_SESSION later,
        old Redis sessions will automatically get those fields.
        """
        session = SessionFactory.create_empty_session()
        session.update(data or {})

        SessionFactory._normalize_nested_defaults(session)
        SessionFactory._clear_volatile_fields(session)

        return session

    @staticmethod
    def session_for_persistence(
        session: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Remove volatile bot fields before saving session to Redis.
        """
        payload = deepcopy(session)

        for field in VOLATILE_SESSION_FIELDS:
            payload.pop(field, None)

        for key in list(payload.keys()):
            if str(key).endswith("_activity_id"):
                payload.pop(key, None)

        return payload

    @staticmethod
    def create_reset_session(
        current_session: dict[str, Any],
        new_language: str | None = None,
        full_reset: bool = False,
    ) -> dict[str, Any]:
        """
        Reset session while preserving requester and conversation context.
        Country/documents/vendor data will be cleared.
        """
        new_session = SessionFactory.create_empty_session()

        SessionFactory._preserve_common_fields(
            source=current_session,
            target=new_session,
        )

        if new_language:
            new_session["user_language"] = new_language
            new_session["language_confirmed"] = True

        if full_reset:
            new_session["welcome_sent"] = False
            new_session["conversation_initialized"] = False

        return new_session

    @staticmethod
    def _build_document_state(
        country_config: dict[str, Any],
    ) -> dict[str, Any]:
        documents: dict[str, Any] = {}

        for document_config in country_config.get("documents", []):
            document_type = document_config["documentType"]

            documents[document_type] = {
                "document_type": document_type,
                "display_name": document_config.get(
                    "displayName",
                    document_type,
                ),
                "required": document_config.get("required", False),
                "allow_multiple": document_config.get("allowMultiple", False),
                "min_files": document_config.get("minFiles", 0),
                "max_files": document_config.get("maxFiles", 1),
                "ocr_required": document_config.get("ocrRequired", False),
                "extract_fields": document_config.get("extractFields", []),
                "validations": document_config.get("validations", {}),

                "files": [],
                "file_hashes": [],
                "sftp_paths": [],

                "ocr_data": {},
                "ocr_confidence": None,

                "validation_result": None,
                "validation_errors": [],

                "status": "pending",
            }

        return documents

    @staticmethod
    def _get_first_required_document(
        documents: dict[str, Any],
    ) -> str | None:
        for document_type, document_state in documents.items():
            if document_state.get("required"):
                return document_type

        return next(iter(documents), None)

    @staticmethod
    def _preserve_common_fields(
        source: dict[str, Any],
        target: dict[str, Any],
    ) -> None:
        for field in PRESERVED_ON_RESET_FIELDS:
            if field in source:
                target[field] = deepcopy(source[field])

    @staticmethod
    def _normalize_nested_defaults(
        session: dict[str, Any],
    ) -> None:
        """
        Make sure nested sections exist even for old Redis sessions.
        """
        for key, default_value in DEFAULT_SESSION.items():
            if key not in session:
                session[key] = deepcopy(default_value)

        for section in ["requester", "vendor", "workflow", "validation", "files"]:
            if section not in session or session[section] is None:
                session[section] = deepcopy(DEFAULT_SESSION[section])

            if isinstance(DEFAULT_SESSION[section], dict):
                for nested_key, nested_default in DEFAULT_SESSION[section].items():
                    session[section].setdefault(
                        nested_key,
                        deepcopy(nested_default),
                    )

    @staticmethod
    @staticmethod
    def _clear_volatile_fields(
        session: dict[str, Any],
    ) -> None:
        for field in VOLATILE_SESSION_FIELDS:
            session[field] = None

        for key in list(session.keys()):
            if str(key).endswith("_activity_id"):
                session[key] = None
 