from sqlalchemy.orm import Session

from fides.api.util.fuzzy_search_utils import (
    add_identity_to_automaton,
    get_decrypted_identities_automaton,
)


class DecryptedIdentityAutomatonMixin:
    """
    A class housing common decrypted identity automaton logic
    """

    def add_identities_to_automaton(self) -> None:
        """
        Manually add identities to automaton. Currently, used only during privacy request creation.

        If the automaton has expired, this method also refreshes the entire automaton.
        """
        db = Session.object_session(self)
        automaton = get_decrypted_identities_automaton(db, True)
        add_identity_to_automaton(automaton, self.id, self.get_persisted_identity().__dict__)  # type: ignore
