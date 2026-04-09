"""Service for resolving actor display names from user_id or client_id."""

from typing import Optional

from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.config import get_config

CONFIG = get_config()


class AttributionService:
    """Service for resolving actor display names.

    Translates user_id or client_id into a human-readable display name.
    Exactly one of user_id or client_id will be set per request — they are
    mutually exclusive (human user XOR API client).
    """

    def __init__(self, db: Session):
        self.db = db

    def get_actor_display_name(
        self,
        *,
        user_id: Optional[str],
        client_id: Optional[str],
        fallback: Optional[str] = None,
    ) -> Optional[str]:
        """Resolve a human-readable display name for the actor that performed an action.

        Args:
            user_id: The user ID of the actor, if a human user.
            client_id: The client ID of the actor, if an API client.
            fallback: Value to return when neither id resolves to a name.

        Returns:
            Display name string, or fallback if not resolvable.
        """
        if user_id:
            if user_id == CONFIG.security.oauth_root_client_id:
                return CONFIG.security.root_username

            user: Optional[FidesUser] = FidesUser.get_by(
                self.db, field="id", value=user_id
            )
            return user.username if user else fallback

        if client_id:
            # Import here to avoid circular imports — ClientDetail lives in oauth models
            from fides.api.models.client import ClientDetail  # noqa: PLC0415

            client: Optional[ClientDetail] = (
                self.db.query(ClientDetail)
                .filter(ClientDetail.id == client_id)
                .first()
            )
            if client:
                return client.name or client_id
            return client_id

        return fallback
