from copy import copy

import pytest
from sqlalchemy.exc import IntegrityError

from fides.api.models.location_regulation_selections import PrivacyNoticeRegion
from fides.api.models.privacy_experience import (
    ComponentType,
    ExperienceTranslation,
    PrivacyExperience,
    PrivacyExperienceConfig,
    PrivacyExperienceConfigHistory,
    upsert_privacy_experiences_after_config_update,
)
from fides.api.schemas.language import SupportedLanguage


class TestExperienceConfig:
    def test_create_privacy_experience_config(self, db, privacy_notice):
        """Assert PrivacyExperienceConfig, a translation, and its historical record are created"""
        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "component": "banner_and_modal",
                "regions": [PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.us_co],
                "privacy_notice_ids": [privacy_notice.id],
                "name": "My New Experience Config",
                "allow_language_selection": False,
                "translations": [
                    {
                        "language": "en",
                        "description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                        "privacy_preferences_link_label": "Manage preferences",
                        "modal_link_label": "Manage my consent preferences",
                        "purpose_header": "We and our partners process data for the following purposes",
                        "privacy_policy_link_label": "View our privacy policy",
                        "privacy_policy_url": "http://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Control your privacy",
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "OK",
                        "banner_description": "We care about your privacy. You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Control Your Privacy",
                        "is_default": True,
                    }
                ],
            },
        )
        assert config.allow_language_selection is False
        assert config.component == ComponentType.banner_and_modal
        assert config.disabled is True
        assert config.dismissable is True
        assert config.name == "My New Experience Config"
        assert config.regions == [
            PrivacyNoticeRegion.us_ca,
            PrivacyNoticeRegion.us_co,
        ]  # Convenience property
        assert config.privacy_notices == [privacy_notice]

        assert len(config.translations) == 1
        translation = config.translations[0]

        assert translation.accept_button_label == "Accept all"
        assert translation.acknowledge_button_label == "OK"
        assert (
            translation.banner_description
            == "We care about your privacy. You can accept, reject, or manage your preferences in detail."
        )
        assert translation.banner_title == "Control Your Privacy"
        assert (
            translation.description
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert translation.experience_config_id == config.id
        assert translation.is_default is True
        assert translation.language == SupportedLanguage.english
        assert translation.privacy_preferences_link_label == "Manage preferences"
        assert translation.modal_link_label == "Manage my consent preferences"
        assert translation.privacy_policy_link_label == "View our privacy policy"
        assert translation.privacy_policy_url == "http://example.com/privacy"
        assert translation.reject_button_label == "Reject all"
        assert translation.save_button_label == "Save"
        assert translation.title == "Control your privacy"
        assert (
            translation.purpose_header
            == "We and our partners process data for the following purposes"
        )
        assert translation.version == 1.0  # Convenience property
        assert (
            translation.experience_config_history == translation.histories.first()
        )  # Convenience property

        assert translation.histories.count() == 1

        # Historical record versions translation and notice combined
        history = translation.histories[0]
        assert translation.privacy_experience_config_history_id == history.id

        assert history.accept_button_label == "Accept all"
        assert history.acknowledge_button_label == "OK"
        assert history.allow_language_selection is False
        assert (
            history.banner_description
            == "We care about your privacy. You can accept, reject, or manage your preferences in detail."
        )
        assert history.banner_title == "Control Your Privacy"
        assert history.component == ComponentType.banner_and_modal
        assert (
            history.description
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert history.disabled is True
        assert config.dismissable is True
        assert history.is_default is True
        assert history.language == SupportedLanguage.english
        assert history.name == "My New Experience Config"
        assert history.origin is None
        assert history.privacy_preferences_link_label == "Manage preferences"
        assert history.modal_link_label == "Manage my consent preferences"
        assert history.privacy_policy_link_label == "View our privacy policy"
        assert history.privacy_policy_url == "http://example.com/privacy"
        assert history.reject_button_label == "Reject all"
        assert history.save_button_label == "Save"
        assert history.title == "Control your privacy"
        assert history.translation_id == translation.id
        assert history.version == 1.0

        translation.delete(db)
        db.refresh(history)
        # When a translation is deleted, we just cascade the translation_id to be none, and leave
        # the historical record intact
        assert history.translation_id is None

        history.delete(db)

        config.delete(db=db)

    def test_update_privacy_experience_config_level(self, db, privacy_notice):
        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "component": "banner_and_modal",
                "regions": [PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.us_co],
                "privacy_notice_ids": [privacy_notice.id],
                "name": "My New Experience Config",
                "allow_language_selection": False,
                "translations": [
                    {
                        "language": SupportedLanguage.english,
                        "description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                        "privacy_preferences_link_label": "Manage preferences",
                        "modal_link_label": "Manage my consent preferences",
                        "privacy_policy_link_label": "View our privacy policy",
                        "privacy_policy_url": "http://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Control your privacy",
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "OK",
                        "banner_description": "We care about your privacy. You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Control Your Privacy",
                    }
                ],
            },
        )
        config_created_at = config.created_at
        config_updated_at = config.updated_at

        orig_count = db.query(PrivacyExperienceConfig).count()
        orig_translation_count = db.query(ExperienceTranslation).count()

        update_data = {
            "component": "banner_and_modal",
            "name": "Updated Privacy Experience Config",
            "allow_language_selection": True,
            "translations": [  # Contrived, only supplying one translation when allow language selection is True
                {
                    "language": SupportedLanguage.english,
                    "description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                    "privacy_preferences_link_label": "Manage preferences",
                    "modal_link_label": "Manage my consent preferences",
                    "privacy_policy_link_label": "View our privacy policy",
                    "privacy_policy_url": "http://example.com/privacy",
                    "reject_button_label": "Reject all",
                    "save_button_label": "Save",
                    "title": "Control your privacy",
                    "accept_button_label": "Accept all",
                    "acknowledge_button_label": "OK",
                    "banner_description": "We care about your privacy. You can accept, reject, or manage your preferences in detail.",
                    "banner_title": "Control Your Privacy",
                }
            ],
        }

        dry_update = config.dry_update(data=update_data)
        # These dry updates aren't bound to a Session, but we want to assert that
        # accessing regions doesn't fail
        assert dry_update.regions == []
        config.dry_update_translations(
            [translation for translation in update_data["translations"]]
        )
        assert orig_count == db.query(PrivacyExperienceConfig).count()
        assert orig_translation_count == db.query(ExperienceTranslation).count()

        config.update(
            db=db,
            data={
                "component": "banner_and_modal",
                "name": "Updated Privacy Experience Config",
                "allow_language_selection": True,
                "translations": [  # Contrived, only supplying one translation when allow language selection is True
                    {
                        "language": SupportedLanguage.english,
                        "description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                        "privacy_preferences_link_label": "Manage preferences",
                        "modal_link_label": "Manage my consent preferences",
                        "privacy_policy_link_label": "View our privacy policy",
                        "privacy_policy_url": "http://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Control your privacy",
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "OK",
                        "banner_description": "We care about your privacy. You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Control Your Privacy",
                    }
                ],
            },
        )
        db.refresh(config)

        # Asserting dry update did not get added to the db
        assert db.query(PrivacyExperienceConfig).count() == orig_count
        assert db.query(ExperienceTranslation).count() == orig_translation_count

        assert config.name == "Updated Privacy Experience Config"
        assert config.allow_language_selection is True
        assert config.created_at == config_created_at
        assert config.updated_at > config_updated_at

        translation = config.translations[0]
        db.refresh(translation)
        assert translation.version == 2.0
        assert translation.histories.count() == 2
        history = translation.histories.order_by(
            PrivacyExperienceConfigHistory.created_at
        )[1]
        assert history.name == "Updated Privacy Experience Config"
        assert history.allow_language_selection is True
        assert translation.privacy_experience_config_history_id == history.id

        old_history = translation.histories.order_by(
            PrivacyExperienceConfigHistory.created_at
        )[0]
        assert old_history.version == 1.0
        assert old_history.name == "My New Experience Config"
        assert old_history.allow_language_selection is False

        translation.delete(db)
        old_history.delete(db)
        history.delete(db)

    def test_update_privacy_experience_config_add_translation(
        self, db, experience_config_banner_and_modal
    ):
        updated_at = experience_config_banner_and_modal.updated_at

        experience_config_banner_and_modal.update(
            db=db,
            data={
                "translations": [
                    {
                        "language": SupportedLanguage.english,
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "Confirm",
                        "banner_description": "You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Manage Your Consent",
                        "description": "On this page you can opt in and out of these data uses cases",
                        "privacy_preferences_link_label": "Manage preferences",
                        "modal_link_label": "Manage my consent preferences",
                        "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                        "privacy_policy_url": "https://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Manage your consent",
                    },
                    {
                        "language": SupportedLanguage.serbian_cyrillic,
                        "accept_button_label": "Прихвати",
                        "acknowledge_button_label": "Потврди",
                        "banner_description": "Можете прихватити, одбити или детаљно управљати својим преференцама.",
                        "banner_title": "Управљајте својим пристанком",
                        "description": "На овој страници можете укључити и искључити ове случајеве коришћења података",
                        "privacy_preferences_link_label": "Управљајте преференцама",
                        "modal_link_label": "Управљај мојим поставкама сагласности",
                        "privacy_policy_link_label": "Погледајте политику приватности наше компаније",
                        "privacy_policy_url": "https://example.com/privacy",
                        "reject_button_label": "Одбаци све",
                        "save_button_label": "сачувати",
                        "title": "Управљајте својим пристанком",
                    },
                ],
            },
        )
        db.refresh(experience_config_banner_and_modal)
        # Experience Config itself wasn't updated, just the translations, so the date is the same
        assert experience_config_banner_and_modal.updated_at == updated_at

        # Nothing changed on the original notice or the first translation, so the historical record is untouched
        assert len(experience_config_banner_and_modal.translations) == 2
        translation = experience_config_banner_and_modal.translations[0]
        assert translation.language == SupportedLanguage.english
        assert translation.histories.count() == 1

        # This is a brand new historical record, because the translation was just added
        translation_gb = experience_config_banner_and_modal.translations[1]
        assert translation_gb.language == SupportedLanguage.serbian_cyrillic
        assert translation_gb.save_button_label == "сачувати"
        assert translation_gb.histories.count() == 1
        assert translation_gb.histories[0].save_button_label == "сачувати"

    def test_update_privacy_experience_config_update_translation(
        self, db, experience_config_banner_and_modal
    ):
        updated_at = experience_config_banner_and_modal.updated_at

        experience_config_banner_and_modal.update(
            db=db,
            data={
                "translations": [
                    {
                        "language": SupportedLanguage.english,
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "Confirm",
                        "banner_description": "You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Manage Your Consent",
                        "description": "On this page you can opt in and out of these data uses cases",
                        "privacy_preferences_link_label": "Manage preferences",
                        "modal_link_label": "Manage my consent preferences",
                        "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                        "privacy_policy_url": "https://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Manage your consent!",
                    }
                ],
            },
        )
        db.refresh(experience_config_banner_and_modal)
        assert experience_config_banner_and_modal.updated_at == updated_at

        assert len(experience_config_banner_and_modal.translations) == 1
        translation = experience_config_banner_and_modal.translations[0]
        assert translation.language == SupportedLanguage.english

        # Translation was updated so we needed a new version
        assert translation.histories.count() == 2
        assert translation.title == "Manage your consent!"
        assert translation.histories.count() == 2

        assert translation.histories[0].title == "Manage your consent"
        assert translation.histories[0].version == 1.0

        assert translation.histories[1].title == "Manage your consent!"
        assert translation.histories[1].version == 2.0

    def test_update_privacy_experience_config_remove_translation(
        self, db, experience_config_banner_and_modal
    ):
        updated_at = copy(experience_config_banner_and_modal.updated_at)

        translation = experience_config_banner_and_modal.translations[0]
        history = translation.histories[0]

        experience_config_banner_and_modal.update(
            db=db,
            data={
                "name": "New name",
                "translations": [],
            },
        )

        assert experience_config_banner_and_modal.updated_at != updated_at
        assert experience_config_banner_and_modal.name == "New name"

        # All translations have been deleted
        assert len(experience_config_banner_and_modal.translations) == 0

        # Historical record still exists for consent reporting but its translation id was set to null
        db.refresh(history)
        assert history.version == 1.0
        assert history.translation_id is None

    def test_update_privacy_experience_config_update_notices(
        self, db, experience_config_banner_and_modal, privacy_notice
    ):
        assert len(experience_config_banner_and_modal.translations) == 1

        assert experience_config_banner_and_modal.privacy_notices == []
        experience_config_banner_and_modal.save(db)

        experience_config_banner_and_modal.update(
            db=db,
            data={
                "privacy_notice_ids": [privacy_notice.id],
                "translations": [
                    {
                        "language": SupportedLanguage.english,
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "Confirm",
                        "banner_description": "You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Manage Your Consent",
                        "description": "On this page you can opt in and out of these data uses cases",
                        "privacy_preferences_link_label": "Manage preferences",
                        "modal_link_label": "Manage my consent preferences",
                        "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                        "privacy_policy_url": "https://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Manage your consent",
                    }
                ],
            },
        )
        db.refresh(experience_config_banner_and_modal)
        assert experience_config_banner_and_modal.privacy_notices == [privacy_notice]

        # Notices linked changed only, which doesn't bump a new version
        db.refresh(experience_config_banner_and_modal)
        assert len(experience_config_banner_and_modal.translations) == 1
        translation = experience_config_banner_and_modal.translations[0]
        assert translation.histories.count() == 1

        experience_config_banner_and_modal.update(
            db=db,
            data={
                "privacy_notice_ids": [],
                "translations": [
                    {
                        "language": SupportedLanguage.english,
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "Confirm",
                        "banner_description": "You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Manage Your Consent",
                        "description": "On this page you can opt in and out of these data uses cases",
                        "privacy_preferences_link_label": "Manage preferences",
                        "modal_link_label": "Manage my consent preferences",
                        "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                        "privacy_policy_url": "https://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Manage your consent",
                    }
                ],
            },
        )

        db.refresh(experience_config_banner_and_modal)
        assert experience_config_banner_and_modal.privacy_notices == []
        db.refresh(experience_config_banner_and_modal)
        assert len(experience_config_banner_and_modal.translations) == 1
        translation = experience_config_banner_and_modal.translations[0]
        assert translation.histories.count() == 1

    def test_update_privacy_experience_config_update_regions(
        self, db, experience_config_banner_and_modal
    ):
        assert experience_config_banner_and_modal.experiences.count() == 0
        updated_at = experience_config_banner_and_modal.updated_at

        experience_config_banner_and_modal.update(
            db=db,
            data={
                "regions": [PrivacyNoticeRegion.us_ca],
                "translations": [
                    {
                        "language": SupportedLanguage.english,
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "Confirm",
                        "banner_description": "You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Manage Your Consent",
                        "description": "On this page you can opt in and out of these data uses cases",
                        "privacy_preferences_link_label": "Manage preferences",
                        "modal_link_label": "Manage my consent preferences",
                        "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                        "privacy_policy_url": "https://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Manage your consent",
                    }
                ],
            },
        )

        db.refresh(experience_config_banner_and_modal)
        assert experience_config_banner_and_modal.regions == [PrivacyNoticeRegion.us_ca]

        exp = experience_config_banner_and_modal.experiences.first()
        exp_id = exp.id

        assert exp.experience_config_id == experience_config_banner_and_modal.id
        assert experience_config_banner_and_modal.updated_at == updated_at

        experience_config_banner_and_modal.update(
            db=db,
            data={
                "regions": [],
                "translations": [
                    {
                        "language": SupportedLanguage.english,
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "Confirm",
                        "banner_description": "You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Manage Your Consent",
                        "description": "On this page you can opt in and out of these data uses cases",
                        "privacy_preferences_link_label": "Manage preferences",
                        "modal_link_label": "Manage my consent preferences",
                        "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                        "privacy_policy_url": "https://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Manage your consent",
                    }
                ],
            },
        )

        db.refresh(experience_config_banner_and_modal)
        assert experience_config_banner_and_modal.regions == []
        assert experience_config_banner_and_modal.experiences.count() == 0

        # Privacy Experience was deleted
        assert (
            db.query(PrivacyExperience).filter(PrivacyExperience.id == exp_id).first()
            is None
        )


class TestPrivacyExperience:
    def test_create_privacy_experience(self, db, experience_config_banner_and_modal):
        """Assert PrivacyExperience is created as expected"""
        exp = PrivacyExperience.create(
            db=db,
            data={
                "region": "us_tx",
                "experience_config_id": experience_config_banner_and_modal.id,
            },
        )

        assert exp.region == PrivacyNoticeRegion.us_tx
        assert exp.experience_config_id == experience_config_banner_and_modal.id
        assert exp.component == ComponentType.banner_and_modal  # Convenience property
        assert exp.experience_config == experience_config_banner_and_modal
        assert exp.show_banner is True  # Convenience property
        assert exp.id is not None

        assert (
            PrivacyExperience.get_experiences_by_region_and_component(
                db, PrivacyNoticeRegion.us_tx, ComponentType.banner_and_modal
            ).first()
            == exp
        )

        exp.delete(db=db)

    @pytest.mark.parametrize(
        "region,country",
        [
            ("us_ca", "us"),
            ("us_tx", "us"),
            ("us", "us"),
            ("ca_qc", "ca"),
            ("ca", "ca"),
            ("fr", "fr"),
        ],
    )
    def test_region_country_property(
        self, db, region, country, experience_config_banner_and_modal
    ):
        exp: PrivacyExperience = PrivacyExperience.create(
            db=db,
            data={
                "region": region,
                "experience_config_id": experience_config_banner_and_modal.id,
            },
        )

        assert exp.region_country == country

        exp.delete(db)


class TestUpsertPrivacyExperiencesOnConfigChange:
    def test_experience_config_created_no_matching_experience_exists(self, db):
        """Test a privacy center ExperienceConfig is created and AK is linked via a PrivacyExperience
        with a FK to PrivacyExperienceConfig
        """
        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "name": "My PC Config",
                "component": "privacy_center",
                "translations": [{"language": "en", "title": "Control your privacy"}],
            },
        )

        assert (
            PrivacyExperience.get_experiences_by_region_and_component(
                db, PrivacyNoticeRegion.us_ak, ComponentType.privacy_center
            ).count()
            == 0
        )

        linked = upsert_privacy_experiences_after_config_update(
            db, config, regions=[PrivacyNoticeRegion.us_ak]
        )

        pc_exps = PrivacyExperience.get_experiences_by_region_and_component(
            db, PrivacyNoticeRegion.us_ak, ComponentType.privacy_center
        )
        assert pc_exps.count() == 1
        privacy_center_experience = pc_exps.first()

        assert privacy_center_experience is not None
        assert linked == [PrivacyNoticeRegion.us_ak]

        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ak
        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.experience_config_id == config.id

        privacy_center_experience.delete(db)
        for translation in config.translations:
            translation.histories[0].delete(db)
            translation.delete(db)
        config.delete(db)

    def test_experience_config_updated_matching_experience_already_linked(self, db):
        """Privacy Center Experience Config updated, and we attempt to add AK to this,
        but it is already linked, so no action needed"""

        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "name": "My other PC Config",
                "component": "privacy_center",
                "translations": [{"language": "en", "title": "Control your privacy"}],
            },
        )

        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "region": "us_ak",
                "experience_config_id": config.id,
            },
        )
        assert pc_exp.experience_config_id == config.id

        assert config.experiences.count() == 1
        assert config.experiences.first() == pc_exp

        upsert_privacy_experiences_after_config_update(
            db, config, regions=[PrivacyNoticeRegion.us_ak]
        )

        assert pc_exp.experience_config_id == config.id

        assert config.experiences.count() == 1
        privacy_center_experience = config.experiences.first()
        assert privacy_center_experience == pc_exp

        db.refresh(privacy_center_experience)

        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ak
        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.experience_config_id == config.id

        privacy_center_experience.delete(db)
        for translation in config.translations:
            translation.histories[0].delete(db)
            translation.delete(db)
        config.delete(db)

    def test_experience_config_unlinks_region(self, db):
        """Privacy Center Experience Config updated, and we attempt to remove the
        regions."""

        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "name": "My other PC config",
                "component": "privacy_center",
                "translations": [{"language": "en", "title": "Control your privacy"}],
            },
        )

        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "region": "us_ak",
                "experience_config_id": config.id,
            },
        )
        pc_exp_id = pc_exp.id

        assert pc_exp.experience_config_id == config.id
        assert config.experiences.count() == 1

        upsert_privacy_experiences_after_config_update(
            db, config, regions=[]  # Empty region list will remove regions
        )

        assert config.experiences.count() == 0

        assert (
            db.query(PrivacyExperience)
            .filter(PrivacyExperience.id == pc_exp_id)
            .count()
            == 0
        )

        for translation in config.translations:
            translation.histories[0].delete(db)
            translation.delete(db)
        config.delete(db)


class TestExperienceTranslation:
    def test_language_must_be_unique(self, db, experience_config_banner_and_modal):
        et = ExperienceTranslation.create(
            db,
            data={
                "language": SupportedLanguage.german,
                "is_default": True,
                "experience_config_id": experience_config_banner_and_modal.id,
            },
        )

        with pytest.raises(IntegrityError):
            ExperienceTranslation.create(
                db,
                data={
                    "language": SupportedLanguage.german,
                    "is_default": True,
                    "experience_config_id": experience_config_banner_and_modal.id,
                },
            )

        et.delete(db)
