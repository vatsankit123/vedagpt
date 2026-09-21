"""
Chat API router.

POST /api/v1/chat   — scripture Q&A with grounded citations
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["chat"])


def _get_chat_service(request: Request) -> ChatService:
    """Extract the ChatService instance injected at app startup."""
    service = request.app.state.chat_service
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service is not initialised.",
        )
    return service


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask a question about the indexed scripture",
    description=(
        "Submit a question and receive a grounded answer from the indexed scripture passages.\n\n"
        "**Educational disclaimer**: Responses may contain errors and should be verified "
        "against the cited edition and, where appropriate, qualified scholars.  "
        "This service does not represent every philosophical or religious tradition."
    ),
)
async def chat(
    body: ChatRequest,
    request: Request,
) -> ChatResponse:
    """
    Execute the RAG pipeline:
    1. Validate the question (handled by Pydantic).
    2. Enforce maximum question length.
    3. Retrieve relevant passages from Qdrant.
    4. Generate an explanation with Claude.
    5. Return citations from retrieved metadata.
    """
    from app.config import get_settings
    settings = get_settings()

    # Enforce configurable maximum question length.
    if len(body.question) > settings.max_question_length:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Question exceeds maximum allowed length of "
                f"{settings.max_question_length} characters."
            ),
        )

    # Log at DEBUG level only — avoid logging full user questions at INFO.
    logger.debug("Chat request received (question_length=%d).", len(body.question))

    service = _get_chat_service(request)

    try:
        response = service.answer(question=body.question, top_k=body.top_k)
    except Exception as exc:
        # Never expose internal details to the caller.
        logger.error("Unhandled error in chat endpoint: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred.  Please try again later.",
        )

    return response
