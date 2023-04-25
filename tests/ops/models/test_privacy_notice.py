import pytest
from sqlalchemy.orm import Session

from fides.api.ops.common_exceptions import ValidationError
from fides.api.ops.models.privacy_notice import (
    PrivacyNotice,
    PrivacyNoticeHistory,
    PrivacyNoticeRegion,
    can_add_new_use,
    check_conflicting_data_uses,
)


class TestPrivacyNoticeModel:
    def test_create(self, db: Session, privacy_notice: PrivacyNotice):
        """
        Ensure our create override works as expected to create a history object
        """
        # our fixture should have created a privacy notice and therefore a similar history object
        assert len(PrivacyNotice.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 1

        history_object = PrivacyNoticeHistory.all(db)[0]
        assert history_object.name == privacy_notice.name
        assert history_object.data_uses == privacy_notice.data_uses
        assert history_object.version == privacy_notice.version
        assert history_object.privacy_notice_id == privacy_notice.id

        # make sure our create method still auto-populates as needed
        assert privacy_notice.created_at is not None
        assert privacy_notice.updated_at is not None
        assert privacy_notice.id is not None

    def test_update_no_updates_no_history(
        self, db: Session, privacy_notice: PrivacyNotice
    ):
        """
        Ensure updating with no real updates doesn't actually add a history record
        """
        assert len(PrivacyNotice.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 1

        old_name = privacy_notice.name
        old_data_uses = privacy_notice.data_uses

        updated_privacy_notice = privacy_notice.update(db, data={})

        # assert our returned object isn't updated
        assert updated_privacy_notice.name == old_name
        assert updated_privacy_notice.data_uses == old_data_uses

        # assert we have expected db records
        assert len(PrivacyNotice.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 1

        db.refresh(privacy_notice)
        assert privacy_notice.name == old_name
        assert privacy_notice.data_uses == old_data_uses
        assert privacy_notice.version == 1.0

        # and let's run thru the same with a "no-op" update rather than empty data
        updated_privacy_notice = privacy_notice.update(db, data={"name": old_name})

        # assert our returned object isn't updated
        assert updated_privacy_notice.name == old_name
        assert updated_privacy_notice.data_uses == old_data_uses

        # assert we have expected db records
        assert len(PrivacyNotice.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 1

        db.refresh(privacy_notice)
        assert privacy_notice.name == old_name
        assert privacy_notice.data_uses == old_data_uses
        assert privacy_notice.version == 1.0

    def test_update(self, db: Session, privacy_notice: PrivacyNotice):
        """
        Evaluate the overriden update functionality
        Specifically look at the history table and version changes
        """
        assert len(PrivacyNotice.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 1

        old_name = privacy_notice.name
        old_data_uses = privacy_notice.data_uses

        updated_privacy_notice = privacy_notice.update(
            db, data={"name": "updated name"}
        )
        # assert our returned object is updated as we expect
        assert updated_privacy_notice.name == "updated name" != old_name
        assert updated_privacy_notice.data_uses == old_data_uses

        # assert we have expected db records
        assert len(PrivacyNotice.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 2

        db.refresh(privacy_notice)
        assert privacy_notice.name == "updated name"
        assert privacy_notice.data_uses == old_data_uses
        assert privacy_notice.version == 2.0

        # make sure our latest entry in history table corresponds to current record
        notice_history = (
            PrivacyNoticeHistory.query(db)
            .filter(PrivacyNoticeHistory.version == 2.0)
            .first()
        )
        assert notice_history.name == "updated name"
        assert notice_history.data_uses == old_data_uses
        assert notice_history.version == 2.0

        # and that previous record hasn't changed
        notice_history = (
            PrivacyNoticeHistory.query(db)
            .filter(PrivacyNoticeHistory.version == 1.0)
            .first()
        )
        assert notice_history.name == old_name
        assert notice_history.data_uses == old_data_uses
        assert notice_history.version == 1.0

        # now try another update to test that subsequent updates work
        # also try specifying two fields on the update, to make sure that works
        updated_privacy_notice = privacy_notice.update(
            db,
            data={
                "name": "updated name again",
                "data_uses": ["data_use_1", "data_use_2"],
            },
        )

        # assert our returned object is updated as we expect
        assert updated_privacy_notice.name == "updated name again"
        assert updated_privacy_notice.data_uses == ["data_use_1", "data_use_2"]

        # assert we have expected db records
        assert len(PrivacyNotice.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 3

        db.refresh(privacy_notice)
        assert privacy_notice.name == "updated name again"
        assert privacy_notice.data_uses == ["data_use_1", "data_use_2"]
        assert privacy_notice.version == 3.0

        # make sure our latest entry in history table corresponds to current record
        notice_history = (
            PrivacyNoticeHistory.query(db)
            .filter(PrivacyNoticeHistory.version == 3.0)
            .first()
        )
        assert notice_history.name == "updated name again"
        assert notice_history.data_uses == ["data_use_1", "data_use_2"]
        assert notice_history.version == 3.0

        # and that previous record hasn't changed
        notice_history = (
            PrivacyNoticeHistory.query(db)
            .filter(PrivacyNoticeHistory.version == 2.0)
            .first()
        )
        assert notice_history.name == "updated name"
        assert notice_history.data_uses == old_data_uses
        assert notice_history.version == 2.0

    def test_dry_update(self, db: Session, privacy_notice: PrivacyNotice):
        old_name = privacy_notice.name
        old_data_uses = privacy_notice.data_uses

        updated_notice = privacy_notice.dry_update(data={"name": "updated name"})
        # ensure our updated field got updated in-memory
        assert updated_notice.name == "updated name" != old_name
        # ensure non-updated fields are present and unchanged
        assert updated_notice.data_uses == old_data_uses

        # now try a list/array field
        updated_notice = privacy_notice.dry_update(
            data={"data_uses": ["data_use_1", "data_use_2"]}
        )
        # ensure our updated field got updated in-memory
        assert updated_notice.data_uses == ["data_use_1", "data_use_2"] != old_data_uses
        # ensure non-updated fields are present and unchanged
        assert updated_notice.name == old_name

        # try more than one field
        updated_notice = privacy_notice.dry_update(
            data={"name": "updated name", "data_uses": ["data_use_1", "data_use_2"]}
        )
        assert updated_notice.name == "updated name" != old_name
        assert updated_notice.data_uses == ["data_use_1", "data_use_2"] != old_data_uses

        # try an empty field
        updated_notice = privacy_notice.dry_update(data={"name": None})
        assert updated_notice.name is None

        # try an empty string
        updated_notice = privacy_notice.dry_update(data={"name": ""})
        assert updated_notice.name == ""

        # try an empty field alongside another field
        updated_notice = privacy_notice.dry_update(
            data={"name": None, "data_uses": ["data_use_1", "data_use_2"]}
        )
        assert updated_notice.name is None
        assert updated_notice.data_uses == ["data_use_1", "data_use_2"]

        # try just passing in an empty object
        updated_notice = privacy_notice.dry_update(data={})
        assert updated_notice.name == old_name
        assert updated_notice.data_uses == old_data_uses

    def test_dry_update_copies_cleanly(
        self, db: Session, privacy_notice: PrivacyNotice
    ):
        """
        Ensure the dry_update method doesn't cleanly provides a "copied" object
        that mimics the update, but does not actually impact the object being operated on
        """

        assert len(PrivacyNotice.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 1
        old_name = privacy_notice.name

        updated_notice = privacy_notice.dry_update(data={"name": "updated name"})
        # ensure our updated field got updated in-memory
        assert updated_notice.name == "updated name" != old_name

        # ensure we still only have one privacy notice in the DB
        assert len(PrivacyNotice.all(db)) == 1
        db.refresh(privacy_notice)
        # and ensure it hasn't been impacted by the update
        assert privacy_notice.name == old_name

        # ensure no PrivacyNoticeHistory entries were created
        assert len(PrivacyNoticeHistory.all(db)) == 1

        # ensure our dry update object is totally dissociated from the original object
        updated_notice.name = "another updated name"
        assert privacy_notice.name == old_name
        db.refresh(privacy_notice)
        assert privacy_notice.name == old_name

    @pytest.mark.parametrize(
        "should_error,new_privacy_notices,existing_privacy_notices",
        [
            (
                True,
                [
                    PrivacyNotice(
                        name="pn_1",
                        data_uses=["advertising"],
                        regions=[PrivacyNoticeRegion.us_ca],
                    )
                ],
                [
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=["advertising"],
                        regions=[PrivacyNoticeRegion.us_ca],
                    )
                ],
            ),
            (
                True,
                [
                    PrivacyNotice(
                        name="pn_1",
                        data_uses=["advertising", "personalize"],
                        regions=[PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.eu_be],
                    )
                ],
                [
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=["advertising", "third_party_sharing"],
                        regions=[PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.us_co],
                    )
                ],
            ),
            (
                True,
                [
                    PrivacyNotice(
                        name="pn_1",
                        data_uses=["advertising", "third_party_sharing"],
                        regions=[PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.eu_be],
                    )
                ],
                [
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=["advertising.first_party", "personalize"],
                        regions=[PrivacyNoticeRegion.us_co, PrivacyNoticeRegion.eu_be],
                    )
                ],
            ),
            (
                True,
                [
                    PrivacyNotice(
                        name="pn_1",
                        data_uses=[
                            "advertising.first_party.contextual",
                            "third_party_sharing",
                        ],
                        regions=[PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.eu_be],
                    )
                ],
                [
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=["advertising.first_party", "personalize"],
                        regions=[PrivacyNoticeRegion.us_co, PrivacyNoticeRegion.eu_be],
                    )
                ],
            ),
            (
                True,
                [
                    PrivacyNotice(
                        name="pn_1",
                        data_uses=["advertising", "third_party_sharing"],
                        regions=[PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.eu_be],
                    )
                ],
                [
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=["advertising.first_party.contextual", "personalize"],
                        regions=[PrivacyNoticeRegion.us_co, PrivacyNoticeRegion.eu_be],
                    )
                ],
            ),
            (
                True,
                [
                    PrivacyNotice(
                        name="pn_1",
                        data_uses=["advertising", "third_party_sharing"],
                        regions=[PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.eu_be],
                    )
                ],
                [
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=["advertising.first_party", "personalize"],
                        regions=[PrivacyNoticeRegion.us_co, PrivacyNoticeRegion.eu_be],
                    )
                ],
            ),
            (
                False,
                [
                    PrivacyNotice(
                        name="pn_1",
                        data_uses=["advertising.third_party", "third_party_sharing"],
                        regions=[PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.eu_be],
                    )
                ],
                [
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=["advertising.first_party", "personalize"],
                        regions=[PrivacyNoticeRegion.us_co, PrivacyNoticeRegion.eu_be],
                    )
                ],
            ),
            (
                False,
                [
                    PrivacyNotice(
                        name="pn_1",
                        data_uses=["advertising", "third_party_sharing"],
                        regions=[PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.us_va],
                    )
                ],
                [
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=["advertising.first_party", "personalize"],
                        regions=[PrivacyNoticeRegion.us_co, PrivacyNoticeRegion.eu_be],
                    )
                ],
            ),
            (
                True,
                [
                    PrivacyNotice(
                        name="pn_1",
                        data_uses=["advertising", "third_party_sharing"],
                        regions=[PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.eu_be],
                    ),
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=["advertising.first_party", "personalize"],
                        regions=[PrivacyNoticeRegion.us_co, PrivacyNoticeRegion.eu_be],
                    ),
                ],
                [],
            ),
            (
                True,
                [
                    PrivacyNotice(
                        name="pn_1",
                        data_uses=["advertising"],
                        regions=[PrivacyNoticeRegion.us_ca],
                    ),
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=["advertising.first_party", "personalize"],
                        regions=[PrivacyNoticeRegion.us_ca],
                    ),
                ],
                [],
            ),
            (
                True,
                [
                    PrivacyNotice(
                        name="pn_1",
                        data_uses=["third_party_sharing", "personalize"],
                        regions=[PrivacyNoticeRegion.us_ca],
                    ),
                ],
                [
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=["advertising.first_party", "personalize"],
                        regions=[PrivacyNoticeRegion.us_ca],
                    ),
                ],
            ),
            (
                True,
                [
                    PrivacyNotice(
                        name="pn_1",
                        data_uses=["third_party_sharing", "personalize"],
                        regions=[PrivacyNoticeRegion.us_ca],
                    ),
                ],
                [
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=[
                            "advertising.first_party",
                            "advertising.third_party",
                        ],
                        regions=[PrivacyNoticeRegion.us_ca],
                    ),
                    PrivacyNotice(
                        name="pn_3",
                        data_uses=[
                            "advertising.first_party",
                            "advertising.third_party",
                        ],
                        regions=[PrivacyNoticeRegion.us_co],
                    ),
                    PrivacyNotice(
                        name="pn_4",
                        data_uses=["personalize"],
                        regions=[PrivacyNoticeRegion.us_ca],
                    ),
                ],
            ),
            (
                True,
                [
                    PrivacyNotice(
                        name="pn_1",
                        data_uses=["third_party_sharing", "personalize"],
                        regions=[PrivacyNoticeRegion.us_ca],
                    ),
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=[
                            "advertising.first_party",
                            "advertising.third_party",
                        ],
                        regions=[PrivacyNoticeRegion.us_ca],
                    ),
                    PrivacyNotice(
                        name="pn_3",
                        data_uses=[
                            "advertising.first_party",
                            "advertising.third_party",
                        ],
                        regions=[PrivacyNoticeRegion.us_co],
                    ),
                    PrivacyNotice(
                        name="pn_4",
                        data_uses=["personalize"],
                        regions=[PrivacyNoticeRegion.us_ca],
                    ),
                ],
                [],
            ),
            (
                False,
                [
                    PrivacyNotice(
                        name="pn_1",
                        data_uses=[
                            "advertising.first_party.contextual",
                            "third_party_sharing",
                        ],
                        regions=[PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.eu_be],
                    )
                ],
                [
                    PrivacyNotice(
                        name="pn_2",
                        disabled=True,
                        data_uses=["advertising.first_party", "personalize"],
                        regions=[PrivacyNoticeRegion.us_co, PrivacyNoticeRegion.eu_be],
                    )
                ],
            ),
            (
                False,
                [
                    PrivacyNotice(
                        name="pn_1",
                        disabled=True,
                        data_uses=[
                            "advertising.first_party.contextual",
                            "third_party_sharing",
                        ],
                        regions=[PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.eu_be],
                    )
                ],
                [
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=["advertising.first_party", "personalize"],
                        regions=[PrivacyNoticeRegion.us_co, PrivacyNoticeRegion.eu_be],
                    )
                ],
            ),
            (
                False,
                [
                    PrivacyNotice(
                        name="pn_1",
                        disabled=True,
                        data_uses=[
                            "advertising.first_party.contextual",
                            "third_party_sharing",
                        ],
                        regions=[PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.eu_be],
                    )
                ],
                [
                    PrivacyNotice(
                        name="pn_2",
                        disabled=True,
                        data_uses=["advertising.first_party", "personalize"],
                        regions=[PrivacyNoticeRegion.us_co, PrivacyNoticeRegion.eu_be],
                    )
                ],
            ),
            (
                False,
                [
                    PrivacyNotice(
                        name="pn_1",
                        disabled=True,
                        data_uses=[
                            "advertising.first_party.contextual",
                            "third_party_sharing",
                        ],
                        regions=[PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.eu_be],
                    ),
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=["advertising.first_party", "personalize"],
                        regions=[PrivacyNoticeRegion.us_co, PrivacyNoticeRegion.eu_be],
                    ),
                ],
                [],
            ),
            (
                False,
                [
                    PrivacyNotice(
                        name="pn_1",
                        data_uses=["advertising.first_party.personalized"],
                        regions=[PrivacyNoticeRegion.us_ca],
                    )
                ],
                [
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=["advertising.third_party.personalized"],
                        regions=[PrivacyNoticeRegion.us_ca],
                    )
                ],
            ),
            (
                False,
                [
                    PrivacyNotice(
                        name="pn_1",
                        data_uses=["advertising.first_party"],
                        regions=[PrivacyNoticeRegion.us_ca],
                    )
                ],
                [
                    PrivacyNotice(
                        name="pn_2",
                        data_uses=["advertising.third_party.personalized"],
                        regions=[PrivacyNoticeRegion.us_ca],
                    )
                ],
            ),
        ],
    )
    def test_conflicting_data_uses(
        self, should_error, new_privacy_notices, existing_privacy_notices
    ):
        if should_error:
            with pytest.raises(ValidationError):
                check_conflicting_data_uses(
                    new_privacy_notices=new_privacy_notices,
                    existing_privacy_notices=existing_privacy_notices,
                )
        else:
            check_conflicting_data_uses(
                new_privacy_notices=new_privacy_notices,
                existing_privacy_notices=existing_privacy_notices,
            )

    def test_calculate_relevant_systems(
        self,
        db,
        system,
        privacy_notice,
        privacy_notice_us_ca_provide,
        privacy_notice_us_co_provide_service_operations,
        privacy_notice_eu_fr_provide_service_frontend_only,
    ):
        """
        privacy_notice fixture: advertising/third party sharing
        privacy_notice_us_ca_provide fixture: provide
        privacy_notice_us_co_provide_service_operations: provide.service.operations
        privacy_notice_eu_fr_provide_service_frontend_only:  provide.service but fe only
        """

        # Only system's data use is advertising
        assert privacy_notice.histories[0].calculate_relevant_systems(db) == [
            system.fides_key
        ], "Exact match on advertising"
        assert (
            privacy_notice_us_ca_provide.histories[0].calculate_relevant_systems(db)
            == []
        )
        assert (
            privacy_notice_us_co_provide_service_operations.histories[
                0
            ].calculate_relevant_systems(db)
            == []
        )
        assert (
            privacy_notice_eu_fr_provide_service_frontend_only.histories[
                0
            ].calculate_relevant_systems(db)
            == []
        )

        system.privacy_declarations[0].update(
            db=db, data={"data_use": "provide.service"}
        )
        assert privacy_notice.histories[0].calculate_relevant_systems(db) == []
        assert privacy_notice_us_ca_provide.histories[0].calculate_relevant_systems(
            db
        ) == [system.fides_key], "Privacy notice data use is a parent of the system"
        assert (
            privacy_notice_us_co_provide_service_operations.histories[
                0
            ].calculate_relevant_systems(db)
            == []
        ), "Privacy notice data use is a child of the system: N/A"
        assert (
            privacy_notice_eu_fr_provide_service_frontend_only.histories[
                0
            ].calculate_relevant_systems(db)
            == []
        ), "This is an exact match but this privacy notice is frontend only"


class TestCanAddNewUse:
    @pytest.mark.parametrize(
        "existing_use,new_use,expected_can_add_result",
        [
            ("a", "a", False),
            ("a", "a.b", False),
            ("a", "a.b.c", False),
            ("a.b.c", "a.b.c", False),
            ("a.b.c", "a.b", False),
            ("a.b.c", "a", False),
            ("a.b", "a.b", False),
            ("a.b", "a", False),
            ("a", "c", True),
            ("a.b", "c.d", True),
            ("a.b", "a.c", True),
            ("a.b.c", "a.b.d", True),
            ("a.b", "a.c.d", True),
            ("a.c.d", "a.b", True),
        ],
    )
    def test_can_add_new_use(self, existing_use, new_use, expected_can_add_result):
        assert can_add_new_use(existing_use, new_use) == expected_can_add_result
