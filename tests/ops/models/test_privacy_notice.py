from sqlalchemy.orm import Session

from fides.api.ops.models.privacy_notice import PrivacyNotice, PrivacyNoticeHistory


class TestPrivacyNoticeModel:
    def test_update_no_updates_no_history(
        self, db: Session, privacy_notice: PrivacyNotice
    ):
        """
        Ensure updating with no real updates doesn't actually add a history record
        """
        assert len(PrivacyNotice.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 0

        old_name = privacy_notice.name
        old_data_uses = privacy_notice.data_uses

        updated_privacy_notice = privacy_notice.update(db, data={})

        # assert our returned object isn't updated
        assert updated_privacy_notice.name == old_name
        assert updated_privacy_notice.data_uses == old_data_uses

        # assert we have expected db records
        assert len(PrivacyNotice.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 0

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
        assert len(PrivacyNoticeHistory.all(db)) == 0

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
        assert len(PrivacyNoticeHistory.all(db)) == 0

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
        assert len(PrivacyNoticeHistory.all(db)) == 1

        db.refresh(privacy_notice)
        assert privacy_notice.name == "updated name"
        assert privacy_notice.data_uses == old_data_uses
        assert privacy_notice.version == 2.0

        notice_history = PrivacyNoticeHistory.all(db)[0]
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
        assert len(PrivacyNoticeHistory.all(db)) == 2

        db.refresh(privacy_notice)
        assert privacy_notice.name == "updated name again"
        assert privacy_notice.data_uses == ["data_use_1", "data_use_2"]
        assert privacy_notice.version == 3.0

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
        assert len(PrivacyNoticeHistory.all(db)) == 0
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
        assert len(PrivacyNoticeHistory.all(db)) == 0

        # ensure our dry update object is totally dissociated from the original object
        updated_notice.name = "another updated name"
        assert privacy_notice.name == old_name
        db.refresh(privacy_notice)
        assert privacy_notice.name == old_name
