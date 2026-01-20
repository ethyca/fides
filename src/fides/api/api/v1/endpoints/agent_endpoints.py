"""
API endpoints for the AI Privacy Analyst Agent feature.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Security
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from fides.api.api import deps
from fides.api.models.agent import (
    AgentConversation,
    AgentEmbedding,
    AgentEmbeddingQueue,
    AgentMessage,
    AgentSettings,
)
from fides.api.models.fides_user import FidesUser
from fides.api.oauth.utils import get_current_user, verify_oauth_client
from fides.api.schemas.agent import (
    AgentSettingsResponse,
    AgentSettingsUpdate,
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
    ConversationWithMessagesResponse,
    EmbeddingStats,
    EmbeddingSyncRequest,
    EmbeddingSyncResponse,
    MessageResponse,
)
from fides.api.util.api_router import APIRouter
from fides.common.api.v1.urn_registry import V1_URL_PREFIX
from fides.config import CONFIG

# URL prefix for agent endpoints - using "plus" prefix to match frontend expectations
AGENT_URL_PREFIX = f"{V1_URL_PREFIX}/plus/agent"

router = APIRouter(tags=["Agent"], prefix=AGENT_URL_PREFIX)


def _get_or_create_user_for_agent(db: Session, current_user: FidesUser) -> str:
    """
    Ensure the current user exists in the database and return their ID.

    The root user (fidesadmin) is a special case - it's not normally stored in the
    database but is instead defined in the config. For agent conversations, we need
    a real user ID that exists in the fidesuser table due to foreign key constraints.

    This function checks if the user exists in the database. If it's the root user
    and doesn't exist yet, we create a minimal database record for them.
    """
    # Check if user already exists in the database
    db_user = db.query(FidesUser).filter(FidesUser.id == current_user.id).first()

    if db_user:
        return db_user.id

    # User doesn't exist - check if this is the root user
    if current_user.id == CONFIG.security.oauth_root_client_id:
        # Create a database record for the root user
        logger.info("Creating database record for root user to enable agent feature")
        root_user = FidesUser(
            id=CONFIG.security.oauth_root_client_id,
            username=CONFIG.security.root_username or "root",
            # Root user doesn't need password fields since auth is handled via config
        )
        db.add(root_user)
        db.commit()
        db.refresh(root_user)
        return root_user.id

    # Non-root user that doesn't exist - this shouldn't happen normally
    raise HTTPException(
        status_code=HTTP_400_BAD_REQUEST,
        detail="User not found in the database. Unable to create conversation.",
    )


# ============================================================================
# Settings endpoints
# ============================================================================


@router.get(
    "/settings",
    dependencies=[Security(verify_oauth_client)],
    response_model=AgentSettingsResponse,
    status_code=HTTP_200_OK,
)
def get_agent_settings(
    *,
    db: Session = Depends(deps.get_db),
) -> AgentSettings:
    """Get the organization-level agent settings."""
    logger.debug("Getting agent settings")
    return AgentSettings.get_or_create(db)


@router.put(
    "/settings",
    dependencies=[Security(verify_oauth_client)],
    response_model=AgentSettingsResponse,
    status_code=HTTP_200_OK,
)
def update_agent_settings(
    *,
    db: Session = Depends(deps.get_db),
    data: AgentSettingsUpdate,
) -> AgentSettings:
    """Update the organization-level agent settings."""
    logger.info("Updating agent settings")
    settings = AgentSettings.get_or_create(db)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)

    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


# ============================================================================
# Conversation endpoints
# ============================================================================


def _get_message_count(db: Session, conversation_id: str) -> int:
    """Helper to get message count for a conversation."""
    return (
        db.query(AgentMessage)
        .filter(AgentMessage.conversation_id == conversation_id)
        .count()
    )


def _conversation_to_response(
    db: Session, conversation: AgentConversation
) -> ConversationResponse:
    """Convert a conversation model to a response schema with message count."""
    return ConversationResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        is_archived=conversation.is_archived,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=_get_message_count(db, conversation.id),
    )


@router.get(
    "/conversations",
    dependencies=[Security(verify_oauth_client)],
    response_model=ConversationListResponse,
    status_code=HTTP_200_OK,
)
def list_conversations(
    *,
    db: Session = Depends(deps.get_db),
    current_user: FidesUser = Depends(get_current_user),
    page: int = 1,
    size: int = 20,
    include_archived: bool = False,
) -> ConversationListResponse:
    """List conversations for the current user."""
    # Ensure user exists in database (creates root user record if needed)
    user_id = _get_or_create_user_for_agent(db, current_user)

    logger.debug(
        "Listing conversations for user {} (page={}, size={}, include_archived={})",
        user_id,
        page,
        size,
        include_archived,
    )

    offset = (page - 1) * size
    conversations = AgentConversation.get_by_user(
        db,
        user_id=user_id,
        include_archived=include_archived,
        limit=size,
        offset=offset,
    )
    total = AgentConversation.count_by_user(
        db, user_id=user_id, include_archived=include_archived
    )

    return ConversationListResponse(
        items=[_conversation_to_response(db, c) for c in conversations],
        total=total,
        page=page,
        size=size,
    )


@router.post(
    "/conversations",
    dependencies=[Security(verify_oauth_client)],
    response_model=ConversationResponse,
    status_code=HTTP_201_CREATED,
)
def create_conversation(
    *,
    db: Session = Depends(deps.get_db),
    current_user: FidesUser = Depends(get_current_user),
    data: ConversationCreate,
) -> ConversationResponse:
    """Create a new conversation."""
    # Ensure user exists in database (creates root user record if needed)
    user_id = _get_or_create_user_for_agent(db, current_user)
    logger.info("Creating new conversation for user {}", user_id)

    conversation = AgentConversation(
        user_id=user_id,
        title=data.title,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return _conversation_to_response(db, conversation)


@router.get(
    "/conversations/{conversation_id}",
    dependencies=[Security(verify_oauth_client)],
    response_model=ConversationWithMessagesResponse,
    status_code=HTTP_200_OK,
)
def get_conversation(
    *,
    db: Session = Depends(deps.get_db),
    current_user: FidesUser = Depends(get_current_user),
    conversation_id: str,
) -> ConversationWithMessagesResponse:
    """Get a conversation with its messages."""
    conversation = db.query(AgentConversation).filter(
        AgentConversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    # Ensure the user owns this conversation
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    messages = conversation.get_messages(db)

    return ConversationWithMessagesResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        is_archived=conversation.is_archived,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[MessageResponse.model_validate(m) for m in messages],
    )


@router.patch(
    "/conversations/{conversation_id}",
    dependencies=[Security(verify_oauth_client)],
    response_model=ConversationResponse,
    status_code=HTTP_200_OK,
)
def update_conversation(
    *,
    db: Session = Depends(deps.get_db),
    current_user: FidesUser = Depends(get_current_user),
    conversation_id: str,
    data: ConversationUpdate,
) -> ConversationResponse:
    """Update a conversation."""
    conversation = db.query(AgentConversation).filter(
        AgentConversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    # Ensure the user owns this conversation
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    logger.info("Updating conversation {}", conversation_id)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(conversation, key, value)

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return _conversation_to_response(db, conversation)


@router.delete(
    "/conversations/{conversation_id}",
    dependencies=[Security(verify_oauth_client)],
    status_code=HTTP_204_NO_CONTENT,
)
def delete_conversation(
    *,
    db: Session = Depends(deps.get_db),
    current_user: FidesUser = Depends(get_current_user),
    conversation_id: str,
) -> None:
    """Delete a conversation."""
    conversation = db.query(AgentConversation).filter(
        AgentConversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    # Ensure the user owns this conversation
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    logger.info("Deleting conversation {}", conversation_id)
    db.delete(conversation)
    db.commit()


# ============================================================================
# Embedding endpoints
# ============================================================================


@router.get(
    "/embeddings/status",
    dependencies=[Security(verify_oauth_client)],
    response_model=EmbeddingStats,
    status_code=HTTP_200_OK,
)
def get_embedding_status(
    *,
    db: Session = Depends(deps.get_db),
) -> EmbeddingStats:
    """Get statistics about the embedding index."""
    logger.debug("Getting embedding status")
    stats = AgentEmbedding.get_stats(db)
    pending_count = AgentEmbeddingQueue.count_pending(db)

    return EmbeddingStats(
        total_embeddings=stats["total_embeddings"],
        by_entity_type=stats["by_entity_type"],
        pending_queue_items=pending_count,
        oldest_updated_at=stats["oldest_updated_at"],
        newest_updated_at=stats["newest_updated_at"],
    )


@router.post(
    "/embeddings/sync",
    dependencies=[Security(verify_oauth_client)],
    response_model=EmbeddingSyncResponse,
    status_code=HTTP_200_OK,
)
def sync_embeddings(
    *,
    db: Session = Depends(deps.get_db),
    data: Optional[EmbeddingSyncRequest] = None,
) -> EmbeddingSyncResponse:
    """
    Trigger a sync of embeddings for the specified entity types.

    This is a placeholder endpoint - the actual implementation would
    queue a background task to update embeddings.
    """
    entity_types = data.entity_types if data and data.entity_types else ["all"]
    logger.info("Triggering embedding sync for entity types: {}", entity_types)

    # TODO: Implement actual embedding sync logic
    # This would typically queue a background task to:
    # 1. Query entities of the specified types
    # 2. Generate embeddings using an LLM
    # 3. Store/update embeddings in the database

    return EmbeddingSyncResponse(
        status="queued",
        message=f"Embedding sync queued for entity types: {', '.join(entity_types)}",
        entity_types=entity_types,
    )
