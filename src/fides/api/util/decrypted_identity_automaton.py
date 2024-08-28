from sqlalchemy.orm import Session

from fides.api.util.fuzzy_search_utils import (
    add_identity_to_automaton,
    get_decrypted_identities_automaton,
)


class DecryptedIdentityAutomatonMixin:
    """
    A class housing common decrypting identity automaton logic for use as a mixin with
    any sqlalchemy model with an ID.
    """

    def add_identities_to_automaton(self) -> None:
        """
        Manually add identities to automaton as they come in via a new privacy request.

        If the automaton has expired, this method also refreshes the entire automaton.
        """
        db = Session.object_session(self)
        automaton = get_decrypted_identities_automaton(db, True)
        add_identity_to_automaton(automaton, self.id, self.get_persisted_identity())  # type: ignore
