from typing import Generator

import pytest
from fideslang.models import Cookies as CookieSchema
from fideslang.validation import FidesValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.experience_notices import ExperienceNotices
from fides.api.models.location_regulation_selections import DeprecatedNoticeRegion
from fides.api.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    NoticeTranslation,
    PrivacyNotice,
    PrivacyNoticeFramework,
    PrivacyNoticeHistory,
    UserConsentPreference,
)
from fides.api.models.sql_models import Cookies, PrivacyDeclaration
from fides.api.schemas.language import SupportedLanguage


class TestPrivacyNoticeModel:
    def test_configured_regions(
        self,
        db,
        privacy_notice,
        privacy_experience_overlay,
        privacy_experience_privacy_center_france,
        privacy_experience_france_tcf_overlay,
    ):
        assert privacy_notice.configured_regions_for_notice == []

        privacy_experience_overlay.experience_config.privacy_notices.append(
            privacy_notice
        )
        privacy_experience_overlay.experience_config.save(db)

        assert privacy_notice.configured_regions_for_notice == ["us_ca"]

        privacy_experience_privacy_center_france.experience_config.privacy_notices.append(
            privacy_notice
        )
        privacy_experience_privacy_center_france.experience_config.save(db)

        assert privacy_notice.configured_regions_for_notice == [
            "fr",
            "us_ca",
        ]

        privacy_experience_france_tcf_overlay.experience_config.privacy_notices.append(
            privacy_notice
        )
        privacy_experience_france_tcf_overlay.experience_config.save(db)

        # no duplicates
        assert privacy_notice.configured_regions_for_notice == [
            "fr",
            "us_ca",
        ]

    def test_calculate_systems_applicable(
        self, db, privacy_notice, system_with_no_uses
    ):
        # No data uses on systems
        assert privacy_notice.calculated_systems_applicable is False

        pd = PrivacyDeclaration.create(
            db=db,
            data={
                "name": "Third Party Sharing",
                "system_id": system_with_no_uses.id,
                "data_categories": ["marketing.advertising"],
                "data_use": "third_party_sharing",
                "data_subjects": ["customer"],
                "dataset_references": None,
                "legal_basis_for_processing": "Consent",
                "egress": None,
                "ingress": None,
                "retention_period": "3",
            },
        )

        # Data use on system matches data use on privacy notice exactly
        assert privacy_notice.calculated_systems_applicable is True

        # Parent data use of system matches privacy notice data use
        pd.data_use = "marketing.advertising.first_party"
        pd.save(db)
        assert privacy_notice.calculated_systems_applicable is True

        # System data use is too broad- doesn't apply to privacy notice
        pd.data_use = "marketing"
        pd.save(db)
        assert privacy_notice.calculated_systems_applicable is False

    def test_create(self, db: Session, privacy_notice: PrivacyNotice):
        """
        Ensure our create override works as expected to create a translation and a history object
        """
        # our fixture should have created a privacy notice and therefore a similar translation and history object
        assert len(PrivacyNotice.all(db)) == 1
        assert len(NoticeTranslation.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 1

        # make sure our create method still auto-populates as needed
        assert privacy_notice.created_at is not None
        assert privacy_notice.updated_at is not None
        assert privacy_notice.id is not None
        assert privacy_notice.consent_mechanism == ConsentMechanism.opt_in
        assert privacy_notice.default_preference == UserConsentPreference.opt_out
        assert privacy_notice.notice_key == "example_privacy_notice_1"

        assert len(privacy_notice.translations) == 1
        translation = privacy_notice.translations[0]
        assert (
            privacy_notice.get_translation_by_language(db, SupportedLanguage.english)
            == translation
        )

        history_object = PrivacyNoticeHistory.all(db)[0]
        assert history_object.name == privacy_notice.name
        assert history_object.data_uses == privacy_notice.data_uses
        assert history_object.version == 1.0
        assert history_object.translation_id == translation.id
        assert history_object.notice_key == privacy_notice.notice_key

        translation.delete(db)
        db.refresh(history_object)

        # Deleting a translation just sets this FK to null, historical record is kept for auditing
        assert history_object.translation_id is None

    def test_default_preference_property(self, privacy_notice):
        assert privacy_notice.consent_mechanism == ConsentMechanism.opt_in
        assert privacy_notice.default_preference == UserConsentPreference.opt_out

        privacy_notice.consent_mechanism = ConsentMechanism.opt_out
        assert privacy_notice.default_preference == UserConsentPreference.opt_in

        privacy_notice.consent_mechanism = ConsentMechanism.notice_only
        assert privacy_notice.default_preference == UserConsentPreference.acknowledge

    def test_update_no_updates_no_history(
        self, db: Session, privacy_notice: PrivacyNotice
    ):
        """
        Ensure updating with no real updates doesn't actually add a history record.

        Note that translations have to be supplied, otherwise they are removed.
        """
        assert len(PrivacyNotice.all(db)) == 1
        assert len(NoticeTranslation.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 1

        old_name = privacy_notice.name
        old_data_uses = privacy_notice.data_uses

        orig_translations = {
            "language": SupportedLanguage.english,
            "title": "Example privacy notice",
            "description": "user&#x27;s description &lt;script /&gt;",
        }

        # Nothing on the privacy notice itself is changing, and the patched translations are identical
        updated_privacy_notice = privacy_notice.update(
            db, data={"translations": [orig_translations]}
        )

        # assert our returned object isn't updated
        assert updated_privacy_notice.name == old_name
        assert updated_privacy_notice.data_uses == old_data_uses
        assert len(updated_privacy_notice.translations) == 1

        # assert we have expected db records
        assert len(PrivacyNotice.all(db)) == 1
        assert len(NoticeTranslation.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 1

        db.refresh(privacy_notice)
        assert privacy_notice.name == old_name
        assert privacy_notice.data_uses == old_data_uses

        # and let's run thru the same with a "no-op" update rather than empty data at the privacy notice level
        # Translations are identical
        updated_privacy_notice = privacy_notice.update(
            db, data={"name": old_name, "translations": [orig_translations]}
        )

        db.refresh(updated_privacy_notice)

        # assert our returned object isn't updated
        assert updated_privacy_notice.name == old_name
        assert updated_privacy_notice.data_uses == old_data_uses

        # assert we have expected db records
        assert len(PrivacyNotice.all(db)) == 1
        assert len(NoticeTranslation.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 1

        db.refresh(privacy_notice)
        assert privacy_notice.name == old_name
        assert privacy_notice.data_uses == old_data_uses

    def test_update_notice_level(self, db: Session, privacy_notice: PrivacyNotice):
        assert len(PrivacyNotice.all(db)) == 1
        assert len(NoticeTranslation.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 1

        old_name = privacy_notice.name
        old_data_uses = privacy_notice.data_uses

        orig_count = db.query(PrivacyNotice).count()
        original_translations_count = db.query(NoticeTranslation).count()

        dry_update_data = {
            "name": "updated name",
            "translations": [
                {
                    "language": SupportedLanguage.english,
                    "title": "Example privacy notice",
                    "description": "user&#x27;s description &lt;script /&gt;",
                }
            ],
        }

        privacy_notice.dry_update(data=dry_update_data)

        updated_privacy_notice = privacy_notice.update(
            db,
            data={
                "name": "updated name",
                "translations": [
                    {
                        "language": SupportedLanguage.english,
                        "title": "Example privacy notice",
                        "description": "user&#x27;s description &lt;script /&gt;",
                    }
                ],
            },
        )

        assert db.query(PrivacyNotice).count() == orig_count
        assert db.query(NoticeTranslation).count() == original_translations_count

        # assert our returned object is updated as we expect
        assert updated_privacy_notice.name == "updated name" != old_name
        assert updated_privacy_notice.data_uses == old_data_uses

        # assert we have expected db records
        assert len(PrivacyNotice.all(db)) == 1
        assert len(NoticeTranslation.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 2

        db.refresh(privacy_notice)
        assert privacy_notice.name == "updated name"
        assert privacy_notice.data_uses == old_data_uses

        assert len(privacy_notice.translations) == 1

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
                "translations": [
                    {
                        "language": SupportedLanguage.english,
                        "title": "Example privacy notice",
                    }
                ],
            },
        )

        # assert our returned object is updated as we expect
        assert updated_privacy_notice.name == "updated name again"
        assert updated_privacy_notice.data_uses == ["data_use_1", "data_use_2"]

        # assert we have expected db records
        assert len(PrivacyNotice.all(db)) == 1
        assert len(NoticeTranslation.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 3

        db.refresh(privacy_notice)
        assert privacy_notice.name == "updated name again"
        assert privacy_notice.data_uses == ["data_use_1", "data_use_2"]
        assert len(privacy_notice.translations) == 1
        translation = privacy_notice.translations[0]
        assert translation.description == "user&#x27;s description &lt;script /&gt;"

        assert translation.privacy_notice_history.version == 3.0

        # make sure our latest entry in history table corresponds to current record
        notice_history = (
            PrivacyNoticeHistory.query(db)
            .filter(PrivacyNoticeHistory.version == 3.0)
            .first()
        )
        assert notice_history.name == "updated name again"
        assert notice_history.data_uses == ["data_use_1", "data_use_2"]
        assert notice_history.version == 3.0
        assert notice_history.description == "user&#x27;s description &lt;script /&gt;"

        # and that previous record hasn't changed
        notice_history = (
            PrivacyNoticeHistory.query(db)
            .filter(PrivacyNoticeHistory.version == 2.0)
            .first()
        )
        assert notice_history.name == "updated name"
        assert notice_history.data_uses == old_data_uses
        assert notice_history.version == 2.0

    def test_update_translations_added(
        self, db: Session, privacy_notice: PrivacyNotice
    ):
        assert len(PrivacyNotice.all(db)) == 1
        assert len(NoticeTranslation.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 1
        privacy_notice_updated_at = privacy_notice.updated_at

        dry_update_data = {
            "translations": [
                {
                    "language": SupportedLanguage.english,
                    "title": "Example privacy notice",
                    "description": "user&#x27;s description &lt;script /&gt;",
                },
                {
                    "language": SupportedLanguage.spanish,
                    "title": "¡Ejemplo de aviso de privacidad!",
                },
            ]
        }
        privacy_notice.dry_update(data=dry_update_data)

        privacy_notice.update(
            db,
            data=dry_update_data,
        )

        # assert we have expected db records
        assert len(PrivacyNotice.all(db)) == 1
        assert len(NoticeTranslation.all(db)) == 2
        assert len(PrivacyNoticeHistory.all(db)) == 2

        db.refresh(privacy_notice)
        # Privacy notice itself unchanged
        assert privacy_notice.updated_at == privacy_notice_updated_at

        assert len(privacy_notice.translations) == 2

        translation = privacy_notice.translations[0]

        # English translation unchanged
        assert translation.language == SupportedLanguage.english
        assert translation.title == "Example privacy notice"
        assert translation.histories.count() == 1
        assert (
            privacy_notice.get_translation_by_language(db, SupportedLanguage.english)
            == translation
        )

        # "Spanish" translation translation added
        translation_es = privacy_notice.translations[1]
        assert translation_es.language == SupportedLanguage.spanish
        assert translation_es.title == "¡Ejemplo de aviso de privacidad!"
        assert translation.histories.count() == 1
        assert (
            privacy_notice.get_translation_by_language(db, SupportedLanguage.spanish)
            == translation_es
        )
        assert privacy_notice.get_translation_by_language(db, None) is None

        # make sure our latest spanish entry in history table corresponds to current record
        notice_history = (
            PrivacyNoticeHistory.query(db)
            .filter(
                PrivacyNoticeHistory.version == 1.0,
                PrivacyNoticeHistory.translation_id == translation_es.id,
            )
            .first()
        )
        assert notice_history.title == "¡Ejemplo de aviso de privacidad!"
        assert notice_history.version == 1.0

        # and that other record hasn't changed
        notice_history = (
            PrivacyNoticeHistory.query(db)
            .filter(
                PrivacyNoticeHistory.version == 1.0,
                PrivacyNoticeHistory.translation_id == translation.id,
            )
            .first()
        )
        assert notice_history.title == "Example privacy notice"
        assert notice_history.version == 1.0

    def test_update_translations_modified(
        self, db: Session, privacy_notice: PrivacyNotice
    ):
        assert len(PrivacyNotice.all(db)) == 1
        assert len(NoticeTranslation.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 1
        privacy_notice_updated_at = privacy_notice.updated_at

        privacy_notice.update(
            db,
            data={
                "translations": [
                    {
                        "language": SupportedLanguage.english,
                        "title": "Example privacy notice with updated title",
                        "description": "user&#x27;s description &lt;script /&gt;",
                    }
                ],
            },
        )

        # assert we have expected db records
        assert len(PrivacyNotice.all(db)) == 1
        assert len(NoticeTranslation.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 2

        db.refresh(privacy_notice)
        # Privacy notice itself unchanged
        assert privacy_notice.updated_at == privacy_notice_updated_at

        assert len(privacy_notice.translations) == 1
        translation = privacy_notice.translations[0]
        # Translation was updated though
        assert translation.title == "Example privacy notice with updated title"

        # make sure our latest entry in history table corresponds to current record
        notice_history = (
            PrivacyNoticeHistory.query(db)
            .filter(PrivacyNoticeHistory.version == 2.0)
            .first()
        )
        assert notice_history.title == "Example privacy notice with updated title"
        assert notice_history.version == 2.0

        # and that previous record hasn't changed
        notice_history = (
            PrivacyNoticeHistory.query(db)
            .filter(PrivacyNoticeHistory.version == 1.0)
            .first()
        )
        assert notice_history.title == "Example privacy notice"
        assert notice_history.version == 1.0

    def test_update_translations_removed(
        self, db: Session, privacy_notice: PrivacyNotice
    ):
        assert len(PrivacyNotice.all(db)) == 1
        assert len(NoticeTranslation.all(db)) == 1
        assert len(PrivacyNoticeHistory.all(db)) == 1
        privacy_notice_updated_at = privacy_notice.updated_at
        history = db.query(PrivacyNoticeHistory).first()
        assert history.translation_id == NoticeTranslation.all(db)[0].id

        privacy_notice.update(
            db,
            data={"name": "New name"},
        )

        # assert we have expected db records
        assert len(PrivacyNotice.all(db)) == 1
        assert len(NoticeTranslation.all(db)) == 0
        assert len(PrivacyNoticeHistory.all(db)) == 1

        db.refresh(privacy_notice)
        assert privacy_notice.name == "New name"
        assert privacy_notice.updated_at != privacy_notice_updated_at

        assert not len(privacy_notice.translations) == 1

        db.refresh(history)
        # Translation id just removed, so it can stay linked to the Privacy Preference History record if applicable
        assert history.translation_id is None

    def test_dry_update(self, privacy_notice: PrivacyNotice):
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
        Ensure the dry_update method cleanly provides a "copied" object
        that mimics the update, but does not actually impact the object being operated on
        """

        assert len(PrivacyNotice.all(db)) == 1
        assert len(NoticeTranslation.all(db)) == 1
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

        assert len(NoticeTranslation.all(db)) == 1

        # ensure no PrivacyNoticeHistory entries were created
        assert len(PrivacyNoticeHistory.all(db)) == 1

        # ensure our dry update object is totally dissociated from the original object
        updated_notice.name = "another updated name"
        assert privacy_notice.name == old_name
        db.refresh(privacy_notice)
        assert privacy_notice.name == old_name

    @pytest.mark.parametrize(
        "privacy_notice_data_use,declaration_cookies,expected_cookies,description",
        [
            (
                ["marketing.advertising", "third_party_sharing"],
                [{"name": "test_cookie"}],
                [CookieSchema(name="test_cookie")],
                "Data uses overlap exactly",
            ),
            (
                ["marketing.advertising.first_party", "third_party_sharing"],
                [{"name": "test_cookie"}],
                [],
                "Privacy notice use more specific than system's.  Too big a leap to assume system should be adjusted here.",
            ),
            (
                ["marketing", "third_party_sharing"],
                [{"name": "test_cookie"}],
                [CookieSchema(name="test_cookie")],
                "Privacy notice use more general than system's, so system's data use is under the scope of the notice",
            ),
            (
                ["marketing.advertising", "third_party_sharing"],
                [{"name": "test_cookie"}, {"name": "another_cookie"}],
                [CookieSchema(name="test_cookie"), CookieSchema(name="another_cookie")],
                "Test multiple cookies",
            ),
            (["marketing.advertising"], [], [], "No cookies returns an empty set"),
        ],
    )
    def test_relevant_cookies(
        self,
        privacy_notice_data_use,
        declaration_cookies,
        expected_cookies,
        description,
        privacy_notice,
        db,
        system,
    ):
        """Test different combinations of data uses and cookies between the Privacy Notice and the Privacy Declaration"""
        db.query(Cookies).delete()
        privacy_notice.data_uses = privacy_notice_data_use
        privacy_notice.save(db)

        privacy_declaration = system.privacy_declarations[0]
        assert privacy_declaration.data_use == "marketing.advertising"

        for cookie in declaration_cookies:
            Cookies.create(
                db,
                data={
                    "name": cookie["name"],
                    "privacy_declaration_id": privacy_declaration.id,
                    "system_id": system.id,
                },
                check_name=False,
            )

        assert [
            CookieSchema.model_validate(cookie) for cookie in privacy_notice.cookies
        ] == expected_cookies, description

    def test_generate_privacy_notice_key(self, privacy_notice):
        assert (
            PrivacyNotice.generate_notice_key("Example Privacy Notice")
            == "example_privacy_notice"
        )

        assert (
            privacy_notice.generate_notice_key(" Name of My Privacy   Notice  ")
            == "name_of_my_privacy_notice"
        )

        with pytest.raises(FidesValidationError):
            privacy_notice.generate_notice_key("Dawn's Bookstore")

        with pytest.raises(FidesValidationError):
            privacy_notice.generate_notice_key("")

        with pytest.raises(Exception):
            privacy_notice.generate_notice_key(1)

    def test_is_gpp(self):
        assert (
            PrivacyNotice(
                name="pn_1",
                notice_key="pn_1",
                data_uses=["marketing.advertising"],
                framework=PrivacyNoticeFramework.gpp_us_national.value,
            ).is_gpp
            is True
        )

        assert (
            PrivacyNotice(
                name="pn_1",
                notice_key="pn_1",
                data_uses=["marketing.advertising"],
                framework=PrivacyNoticeFramework.gpp_us_state.value,
            ).is_gpp
            is True
        )

        assert (
            PrivacyNotice(
                name="pn_1",
                notice_key="pn_1",
                data_uses=["marketing.advertising"],
                framework="bogus_framework",
            ).is_gpp
            is False
        )

        assert (
            PrivacyNotice(
                name="pn_1",
                notice_key="pn_1",
                data_uses=["marketing.advertising"],
            ).is_gpp
            is False
        )

    def test_deprecated_privacy_notice_region_fields(self, db):
        historic_privacy_notice = PrivacyNoticeHistory.create(
            db,
            data={
                "name": "Deprecated Notice History",
                "description": "old_description",
                "regions": ["gb_eng"],  # deprecated field with deprecated region
                "displayed_in_overlay": True,  # deprecated field
                "displayed_in_privacy_center": True,  # deprecated field
                "displayed_in_api": None,  # deprecated field
                "consent_mechanism": ConsentMechanism.opt_in,
                "data_uses": ["marketing"],
                "version": 1.0,
                "disabled": True,
                "has_gpc_flag": False,
                "enforcement_level": EnforcementLevel.system_wide,
                "notice_key": "test_key",
                "language": None,  # New field, not required for early records
                "title": "Test title",
                "translation_id": None,  # New concept, not required for early records
            },
        )

        assert historic_privacy_notice.regions == [DeprecatedNoticeRegion.gb_eng]
        assert not historic_privacy_notice.language
        assert historic_privacy_notice.displayed_in_privacy_center
        assert historic_privacy_notice.displayed_in_overlay
        assert (
            historic_privacy_notice.displayed_in_api is None
        )  # displayed_in fields are deprecated and not required

    def test_duplicate_notice_translations_prevented(
        self, db, privacy_notice, privacy_experience_overlay
    ):
        config = privacy_experience_overlay.experience_config
        ExperienceNotices.create(
            db, data={"notice_id": privacy_notice.id, "experience_config_id": config.id}
        )

        with pytest.raises(IntegrityError):
            ExperienceNotices.create(
                db,
                data={
                    "notice_id": privacy_notice.id,
                    "experience_config_id": config.id,
                },
            )

    def test_language_must_be_unique(self, db, privacy_notice):
        nt = NoticeTranslation.create(
            db,
            data={
                "language": SupportedLanguage.german,
                "title": "new",
                "privacy_notice_id": privacy_notice.id,
            },
        )

        with pytest.raises(IntegrityError):
            nt = NoticeTranslation.create(
                db,
                data={
                    "language": SupportedLanguage.german,
                    "title": "new",
                    "privacy_notice_id": privacy_notice.id,
                },
            )

        nt.delete(db)


class TestHierarchicalNotices:
    @pytest.fixture(scope="function")
    def child_privacy_notice(self, db: Session) -> Generator:
        privacy_notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "Weekly Ads",
                "notice_key": "weekly_ads_privacy_notice",
                "consent_mechanism": ConsentMechanism.opt_in,
                "data_uses": ["marketing.advertising", "third_party_sharing"],
                "enforcement_level": EnforcementLevel.system_wide,
                "translations": [
                    {
                        "language": "en",
                        "title": "Weekly Ads",
                        "description": "Weekly specials",
                    }
                ],
            },
        )

        yield privacy_notice

        for translation in privacy_notice.translations:
            for history in translation.histories:
                history.delete(db)
            translation.delete(db)
        privacy_notice.delete(db)

    @pytest.fixture(scope="function")
    def second_child_privacy_notice(self, db: Session) -> Generator:
        privacy_notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "Daily Ads",
                "notice_key": "daily_ads_privacy_notice",
                "consent_mechanism": ConsentMechanism.opt_in,
                "data_uses": ["marketing.advertising", "third_party_sharing"],
                "enforcement_level": EnforcementLevel.system_wide,
                "translations": [
                    {
                        "language": "en",
                        "title": "Daily Ads",
                        "description": "Daily specials",
                    }
                ],
            },
        )

        yield privacy_notice

        for translation in privacy_notice.translations:
            for history in translation.histories:
                history.delete(db)
            translation.delete(db)
        privacy_notice.delete(db)

    @pytest.fixture(scope="function")
    def privacy_notice_with_child(
        self, db, child_privacy_notice: PrivacyNotice
    ) -> Generator:
        privacy_notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "example privacy notice",
                "notice_key": "example_privacy_notice_1",
                "consent_mechanism": ConsentMechanism.opt_in,
                "data_uses": ["marketing.advertising", "third_party_sharing"],
                "enforcement_level": EnforcementLevel.system_wide,
                "translations": [
                    {
                        "language": "en",
                        "title": "Example privacy notice",
                        "description": "user&#x27;s description &lt;script /&gt;",
                    }
                ],
                "children": [
                    {"id": child_privacy_notice.id, "name": child_privacy_notice.name}
                ],
            },
        )

        yield privacy_notice

        for translation in privacy_notice.translations:
            for history in translation.histories:
                history.delete(db)
            translation.delete(db)
        privacy_notice.delete(db)

    def test_create_with_child_notice(self, db, child_privacy_notice: PrivacyNotice):
        privacy_notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "example privacy notice",
                "notice_key": "example_privacy_notice_1",
                "consent_mechanism": ConsentMechanism.opt_in,
                "data_uses": ["marketing.advertising", "third_party_sharing"],
                "enforcement_level": EnforcementLevel.system_wide,
                "translations": [
                    {
                        "language": "en",
                        "title": "Example privacy notice",
                        "description": "user&#x27;s description &lt;script /&gt;",
                    }
                ],
                "children": [
                    {"id": child_privacy_notice.id, "name": child_privacy_notice.name}
                ],
            },
        )
        assert privacy_notice.children == [child_privacy_notice]

    def test_create_with_multiple_child_notices(
        self,
        db,
        child_privacy_notice: PrivacyNotice,
        second_child_privacy_notice: PrivacyNotice,
    ):
        privacy_notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "example privacy notice",
                "notice_key": "example_privacy_notice_1",
                "consent_mechanism": ConsentMechanism.opt_in,
                "data_uses": ["marketing.advertising", "third_party_sharing"],
                "enforcement_level": EnforcementLevel.system_wide,
                "translations": [
                    {
                        "language": "en",
                        "title": "Example privacy notice",
                        "description": "user&#x27;s description &lt;script /&gt;",
                    }
                ],
                "children": [
                    {"id": child_privacy_notice.id, "name": child_privacy_notice.name},
                    {
                        "id": second_child_privacy_notice.id,
                        "name": second_child_privacy_notice.name,
                    },
                ],
            },
        )
        assert set(privacy_notice.children) == {
            child_privacy_notice,
            second_child_privacy_notice,
        }

    @pytest.mark.usefixtures("privacy_notice_with_child")
    def test_create_with_already_linked_child_notice(
        self, db, child_privacy_notice: PrivacyNotice
    ):
        with pytest.raises(ValueError) as exc:
            PrivacyNotice.create(
                db=db,
                data={
                    "name": "example privacy notice",
                    "notice_key": "example_privacy_notice_1",
                    "consent_mechanism": ConsentMechanism.opt_in,
                    "data_uses": ["marketing.advertising", "third_party_sharing"],
                    "enforcement_level": EnforcementLevel.system_wide,
                    "translations": [
                        {
                            "language": "en",
                            "title": "Example privacy notice",
                            "description": "user&#x27;s description &lt;script /&gt;",
                        }
                    ],
                    "children": [
                        {
                            "id": child_privacy_notice.id,
                            "name": child_privacy_notice.name,
                        }
                    ],
                },
            )
        assert (
            f"The following notices are already linked to another notice: {child_privacy_notice.name}"
            in str(exc)
        )

    def test_create_with_missing_child_notice(self, db):
        with pytest.raises(ValueError) as exc:
            PrivacyNotice.create(
                db=db,
                data={
                    "name": "example privacy notice",
                    "notice_key": "example_privacy_notice_1",
                    "consent_mechanism": ConsentMechanism.opt_in,
                    "data_uses": ["marketing.advertising", "third_party_sharing"],
                    "enforcement_level": EnforcementLevel.system_wide,
                    "translations": [
                        {
                            "language": "en",
                            "title": "Example privacy notice",
                            "description": "user&#x27;s description &lt;script /&gt;",
                        }
                    ],
                    "children": [{"id": "1", "name": "Daily Ads"}],
                },
            )
        assert "The following notices do not exist: Daily Ads" in str(exc)

    def test_update_with_child_notice(
        self, db, privacy_notice: PrivacyNotice, child_privacy_notice: PrivacyNotice
    ):
        privacy_notice.update(
            db,
            data={
                "translations": [
                    {
                        "language": "en",
                        "title": "Example privacy notice",
                        "description": "user&#x27;s description &lt;script /&gt;",
                    }
                ],
                "children": [
                    {"id": child_privacy_notice.id, "name": child_privacy_notice.name}
                ],
            },
        )
        assert privacy_notice.children == [child_privacy_notice]

    def test_update_with_multiple_child_notices(
        self,
        db,
        privacy_notice: PrivacyNotice,
        child_privacy_notice: PrivacyNotice,
        second_child_privacy_notice: PrivacyNotice,
    ):
        privacy_notice.update(
            db,
            data={
                "translations": [
                    {
                        "language": "en",
                        "title": "Example privacy notice",
                        "description": "user&#x27;s description &lt;script /&gt;",
                    }
                ],
                "children": [
                    {"id": child_privacy_notice.id, "name": child_privacy_notice.name},
                    {
                        "id": second_child_privacy_notice.id,
                        "name": second_child_privacy_notice.name,
                    },
                ],
            },
        )
        assert set(privacy_notice.children) == {
            child_privacy_notice,
            second_child_privacy_notice,
        }

    @pytest.mark.usefixtures("privacy_notice_with_child")
    def test_update_with_already_linked_child_notice(
        self, db, privacy_notice: PrivacyNotice, child_privacy_notice: PrivacyNotice
    ):
        with pytest.raises(ValueError) as exc:
            privacy_notice.update(
                db,
                data={
                    "translations": [
                        {
                            "language": "en",
                            "title": "Example privacy notice",
                            "description": "user&#x27;s description &lt;script /&gt;",
                        }
                    ],
                    "children": [
                        {
                            "id": child_privacy_notice.id,
                            "name": child_privacy_notice.name,
                        }
                    ],
                },
            )
        assert (
            f"The following notices are already linked to another notice: {child_privacy_notice.name}"
            in str(exc)
        )

    def test_update_with_missing_child_notice(self, db, privacy_notice):
        with pytest.raises(ValueError) as exc:
            privacy_notice.update(
                db,
                data={
                    "translations": [
                        {
                            "language": "en",
                            "title": "Example privacy notice",
                            "description": "user&#x27;s description &lt;script /&gt;",
                        }
                    ],
                    "children": [
                        {
                            "id": "1",
                            "name": "Daily Ads",
                        }
                    ],
                },
            )
        assert "The following notices do not exist: Daily Ads" in str(exc)

    def test_unlink_single_child_notice(
        self,
        db,
        privacy_notice_with_child: PrivacyNotice,
        child_privacy_notice: PrivacyNotice,
        second_child_privacy_notice: PrivacyNotice,
    ):
        privacy_notice_with_child.update(
            db,
            data={
                "translations": [
                    {
                        "language": "en",
                        "title": "Example privacy notice",
                        "description": "user&#x27;s description &lt;script /&gt;",
                    }
                ],
                "children": [
                    {"id": child_privacy_notice.id, "name": child_privacy_notice.name},
                    {
                        "id": second_child_privacy_notice.id,
                        "name": second_child_privacy_notice.name,
                    },
                ],
            },
        )
        assert set(privacy_notice_with_child.children) == {
            child_privacy_notice,
            second_child_privacy_notice,
        }

        privacy_notice_with_child.update(
            db,
            data={
                "translations": [
                    {
                        "language": "en",
                        "title": "Example privacy notice",
                        "description": "user&#x27;s description &lt;script /&gt;",
                    }
                ],
                "children": [
                    {"id": child_privacy_notice.id, "name": child_privacy_notice.name}
                ],
            },
        )
        assert privacy_notice_with_child.children == [child_privacy_notice]

    def test_unlink_all_child_notices(
        self,
        db,
        privacy_notice_with_child: PrivacyNotice,
        child_privacy_notice: PrivacyNotice,
    ):
        privacy_notice_with_child.update(
            db,
            data={
                "translations": [
                    {
                        "language": "en",
                        "title": "Example privacy notice",
                        "description": "user&#x27;s description &lt;script /&gt;",
                    }
                ],
                "children": [],
            },
        )
        assert privacy_notice_with_child.children == []

        # verify child privacy notice is just unlinked, not deleted
        assert (
            db.query(PrivacyNotice)
            .filter(PrivacyNotice.id == child_privacy_notice.id)
            .first()
        )

    def test_delete_child_notice(
        self,
        db,
        privacy_notice_with_child: PrivacyNotice,
        child_privacy_notice: PrivacyNotice,
    ):
        # delete the child privacy notice
        for translation in child_privacy_notice.translations:
            for history in translation.histories:
                history.delete(db)
            translation.delete(db)
        child_privacy_notice.delete(db)

        # verify it's removed from the parent
        db.refresh(privacy_notice_with_child)
        assert privacy_notice_with_child.children == []

    def test_delete_parent_notice(
        self,
        db,
        privacy_notice_with_child: PrivacyNotice,
        child_privacy_notice: PrivacyNotice,
    ):
        # delete the parent privacy notice
        for translation in privacy_notice_with_child.translations:
            for history in translation.histories:
                history.delete(db)
            translation.delete(db)
        privacy_notice_with_child.delete(db)

        # verify the child is unlinked but not deleted
        db.refresh(child_privacy_notice)
        assert child_privacy_notice.parent_id is None
