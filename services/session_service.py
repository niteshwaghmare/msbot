"""
Session service module for Vendor Onboarding.

This module provides a Redis-backed session service for managing user
conversation state in the Vendor Onboarding Teams bot flow.

The service is designed to be:
    - Class based.
    - Redis backed.
    - Free from in-memory session cache.
    - Country/document driven.
    - Independent of country-specific document names.

The service uses SessionFactory to create and transform session objects and
RedisService to persist session state.

Session shape:
    session["requester"]   -> requester identity details
    session["vendor"]      -> vendor-related information
    session["documents"]   -> dynamic document state by document type
    session["workflow"]    -> current workflow stage and step
    session["validation"]  -> validation outputs and manual-review status

Example:
    France session:
        session["documents"]["KIBS"]
        session["documents"]["RIB"]

    US session:
        session["documents"]["W9"]
        session["documents"]["BANK_PROOF"]
        session["documents"]["VENDOR_FORM"]

Responsibilities:
    - Load session from Redis.
    - Save session to Redis.
    - Initialize country-specific session state.
    - Reset session while preserving requester context.
    - Delete session.
    - Update requester, vendor, workflow, and document state.
    - Keep orchestration logic separate from Redis connection logic.

This module should not create Redis clients directly.
All Redis operations should go through redis_service.

# When user selects country
country_config = vendor_config["countries"]["FR"]
session = session_service.initialize_country_session(
    conversation_id=conversation_id,
    country_code="FR",
    country_config=country_config,
)

# It creates:
session["documents"] = {
    "KIBS": {...},
    "RIB": {...}
}


# Usage Example
session_service.set_requester(
    conversation_id=conversation_id,
    llid="johndoe",
    email="johndoe@example.com",
    name="John Doe",
)
session_service.add_document_file(
    conversation_id=conversation_id,
    document_type="RIB",
    file_info={
        "file_name": "rib.pdf",
        "path": "/tmp/rib.pdf",
        "sftp_path": "/vendor/fr/rib.pdf",
        "hash": "abc123",
    },
)
"""


from __future__ import annotations

from typing import Any

from core.config import settings
from core.logging import get_logger
from services.redis_service import redis_service
from services.session_factory import SessionFactory

logger = get_logger(__name__)


class SessionService:

    """
    Redis-backed session manager.

    SessionService controls how session state is loaded, saved, reset, and
    updated during the bot conversation flow.

    The service does not keep an in-memory dictionary of sessions. Each read
    operation loads the latest session from Redis, and each write operation
    persists the updated session back to Redis.

    This makes the service suitable for cloud/container deployments where:
        - multiple app replicas may exist
        - local memory is not shared
        - container restarts can happen
        - session state must be centralized

    The service is country/document driven. Document-specific state is managed
    under session["documents"][document_type], allowing new country onboarding
    without changing session fields.

    Example:
        session_service.initialize_country_session(
            conversation_id="abc123",
            country_code="FR",
            country_config=fr_config,
        )

        session_service.add_document_file(
            conversation_id="abc123",
            document_type="RIB",
            file_info=file_info,
        )
    """


    def get_session(
        self,
        conversation_id: str,
    ) -> dict[str, Any]:
        key = self._get_key(conversation_id)

        raw_data = redis_service.get_json(key)

        if not raw_data:
            session = SessionFactory.create_empty_session()
            self.save_session(conversation_id, session)

            logger.info(
                "New empty session created",
                extra={
                    "component": "session",
                    "conversation_id": conversation_id,
                },
            )

            return session

        session = SessionFactory.restore_session(raw_data)

        logger.info(
            "Session loaded from Redis",
            extra={
                "component": "session",
                "conversation_id": conversation_id,
                "country": session.get("country"),
            },
        )

        return session

    def save_session(
        self,
        conversation_id: str,
        session: dict[str, Any],
    ) -> None:
        key = self._get_key(conversation_id)

        payload = SessionFactory.session_for_persistence(session)

        redis_service.set_json(
            key=key,
            value=payload,
            ttl=settings.session.ttl_seconds,
        )

        logger.info(
            "Session saved to Redis",
            extra={
                "component": "session",
                "conversation_id": conversation_id,
                "ttl_seconds": settings.session.ttl_seconds,
                "country": session.get("country"),
            },
        )

    def initialize_country_session(
        self,
        conversation_id: str,
        country_code: str,
        country_config: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Initialize session after user selects country.

        This creates dynamic document state based on country config.
        """
        existing_session = self.get_session(conversation_id)

        session = SessionFactory.create_country_session(
            country_code=country_code,
            country_config=country_config,
            existing_session=existing_session,
        )

        self.save_session(conversation_id, session)

        logger.info(
            "Country session initialized",
            extra={
                "component": "session",
                "conversation_id": conversation_id,
                "country": country_code,
                "document_types": list(session.get("documents", {}).keys()),
            },
        )

        return session

    def reset_session(
        self,
        conversation_id: str,
        new_language: str | None = None,
        full_reset: bool = False,
    ) -> dict[str, Any]:
        """
        Reset session while preserving requester and language context.
        """
        current_session = self.get_session(conversation_id)

        new_session = SessionFactory.create_reset_session(
            current_session=current_session,
            new_language=new_language,
            full_reset=full_reset,
        )

        self.save_session(conversation_id, new_session)

        logger.info(
            "Session reset completed",
            extra={
                "component": "session",
                "conversation_id": conversation_id,
                "full_reset": full_reset,
            },
        )

        return new_session

    def delete_session(
        self,
        conversation_id: str,
    ) -> None:
        key = self._get_key(conversation_id)
        redis_service.delete(key)

        logger.info(
            "Session deleted from Redis",
            extra={
                "component": "session",
                "conversation_id": conversation_id,
            },
        )

    def update_session(
        self,
        conversation_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Update session using shallow top-level merge.
        For deeply nested updates, use dedicated helper methods.
        """
        session = self.get_session(conversation_id)
        session.update(updates)

        self.save_session(conversation_id, session)

        return session

    def set_requester(
        self,
        conversation_id: str,
        llid: str | None = None,
        email: str | None = None,
        name: str | None = None,
    ) -> dict[str, Any]:
        session = self.get_session(conversation_id)

        session["requester"]["llid"] = llid or session["requester"].get("llid")
        session["requester"]["email"] = email or session["requester"].get("email")
        session["requester"]["name"] = name or session["requester"].get("name")

        self.save_session(conversation_id, session)

        return session

    def update_vendor(
        self,
        conversation_id: str,
        vendor_updates: dict[str, Any],
    ) -> dict[str, Any]:
        session = self.get_session(conversation_id)

        session["vendor"].update(vendor_updates)

        self.save_session(conversation_id, session)

        return session

    def add_document_file(
        self,
        conversation_id: str,
        document_type: str,
        file_info: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Add uploaded file info against dynamic document type.

        Example document_type:
            FR: KIBS, RIB
            US: W9, BANK_PROOF, VENDOR_FORM
        """
        session = self.get_session(conversation_id)

        document = self._get_document_or_raise(session, document_type)

        if not document.get("allow_multiple") and document.get("files"):
            raise ValueError(
                f"Document {document_type} does not allow multiple files"
            )

        max_files = document.get("max_files")

        if max_files is not None and len(document["files"]) >= max_files:
            raise ValueError(
                f"Document {document_type} allows maximum {max_files} files"
            )

        document["files"].append(file_info)
        document["status"] = "uploaded"

        file_hash = file_info.get("hash")

        if file_hash:
            document["file_hashes"].append(file_hash)

        sftp_path = file_info.get("sftp_path")

        if sftp_path:
            document["sftp_paths"].append(sftp_path)

        self.save_session(conversation_id, session)

        return session

    def set_document_ocr_data(
        self,
        conversation_id: str,
        document_type: str,
        ocr_data: dict[str, Any],
        ocr_confidence: float | None = None,
    ) -> dict[str, Any]:
        session = self.get_session(conversation_id)

        document = self._get_document_or_raise(session, document_type)

        document["ocr_data"] = ocr_data
        document["ocr_confidence"] = ocr_confidence
        document["status"] = "ocr_completed"

        self.save_session(conversation_id, session)

        return session

    def set_document_validation_result(
        self,
        conversation_id: str,
        document_type: str,
        validation_result: dict[str, Any],
        validation_errors: list[str] | None = None,
    ) -> dict[str, Any]:
        session = self.get_session(conversation_id)

        document = self._get_document_or_raise(session, document_type)

        document["validation_result"] = validation_result
        document["validation_errors"] = validation_errors or []

        document["status"] = (
            "validation_failed"
            if validation_errors
            else "validated"
        )

        self.save_session(conversation_id, session)

        return session

    def update_workflow(
        self,
        conversation_id: str,
        stage: str | None = None,
        current_step: str | None = None,
    ) -> dict[str, Any]:
        session = self.get_session(conversation_id)

        if stage:
            session["workflow"]["stage"] = stage

        if current_step:
            session["workflow"]["current_step"] = current_step

        if stage:
            completed_steps = session["workflow"].setdefault(
                "completed_steps",
                [],
            )

            if stage not in completed_steps:
                completed_steps.append(stage)

        self.save_session(conversation_id, session)

        return session

    def _get_document_or_raise(
        self,
        session: dict[str, Any],
        document_type: str,
    ) -> dict[str, Any]:
        documents = session.get("documents", {})

        if document_type not in documents:
            available_documents = list(documents.keys())

            raise KeyError(
                f"Document type {document_type} not configured for country "
                f"{session.get('country')}. Available documents: {available_documents}"
            )

        return documents[document_type]

    def _get_key(
        self,
        conversation_id: str,
    ) -> str:
        safe_conversation_id = self._sanitize_conversation_id(conversation_id)
        return f"{settings.session.key_prefix}{safe_conversation_id}"

    @staticmethod
    def _sanitize_conversation_id(
        conversation_id: str,
    ) -> str:
        return "".join(
            char
            for char in conversation_id
            if char.isalnum() or char in ("-", "_", ".")
        )


session_service = SessionService()