from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.location_regulation_selections import PrivacyNoticeRegion
from fides.api.models.privacy_experience import (
    PrivacyExperience,
    PrivacyExperienceConfig,
)


@pytest.fixture(scope="function")
def experience_config_modal(db: Session) -> Generator:
    exp = PrivacyExperienceConfig.create(
        db=db,
        data={
            "component": "modal",
            "regions": [PrivacyNoticeRegion.it],
            "disabled": False,
            "name": "Experience Config Modal",
            "translations": [
                {
                    "language": "en",
                    "reject_button_label": "Reject all",
                    "save_button_label": "Save",
                    "title": "Control your privacy",
                    "accept_button_label": "Accept all",
                    "description": "user&#x27;s description &lt;script /&gt;",
                }
            ],
        },
    )
    yield exp
    for translation in exp.translations:
        for history in translation.histories:
            history.delete(db)
        translation.delete(db)

    exp.delete(db)


@pytest.fixture(scope="function")
def experience_config_privacy_center(db: Session) -> Generator:
    exp = PrivacyExperienceConfig.create(
        db=db,
        data={
            "component": "privacy_center",
            "name": "Privacy Center config",
            "translations": [
                {
                    "language": "en",
                    "reject_button_label": "Reject all",
                    "save_button_label": "Save",
                    "title": "Control your privacy",
                    "accept_button_label": "Accept all",
                    "description": "user&#x27;s description &lt;script /&gt;",
                }
            ],
        },
    )
    yield exp
    for translation in exp.translations:
        for history in translation.histories:
            history.delete(db)
        translation.delete(db)

    exp.delete(db)


@pytest.fixture(scope="function")
def privacy_experience_privacy_center(
    db: Session, experience_config_privacy_center
) -> Generator:
    privacy_experience = PrivacyExperience.create(
        db=db,
        data={
            "region": PrivacyNoticeRegion.us_co,
            "experience_config_id": experience_config_privacy_center.id,
        },
    )

    yield privacy_experience
    privacy_experience.delete(db)


@pytest.fixture(scope="function")
def experience_config_banner_and_modal(db: Session) -> Generator:
    config = PrivacyExperienceConfig.create(
        db=db,
        data={
            "component": "banner_and_modal",
            "allow_language_selection": False,
            "name": "Banner and modal config",
            "translations": [
                {
                    "language": "en",
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

    yield config
    for translation in config.translations:
        for history in translation.histories:
            history.delete(db)
        translation.delete(db)

    config.delete(db)


@pytest.fixture(scope="function")
def experience_config_tcf_overlay(db: Session) -> Generator:
    config = PrivacyExperienceConfig.create(
        db=db,
        data={
            "component": "tcf_overlay",
            "name": "TCF Config",
            "translations": [
                {
                    "language": "en",
                    "privacy_preferences_link_label": "Manage preferences",
                    "modal_link_label": "Manage my consent preferences",
                    "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                    "privacy_policy_url": "https://example.com/privacy",
                    "reject_button_label": "Reject all",
                    "save_button_label": "Save",
                    "title": "Manage your consent",
                    "description": "On this page you can opt in and out of these data uses cases",
                    "accept_button_label": "Accept all",
                    "acknowledge_button_label": "Confirm",
                    "banner_description": "You can accept, reject, or manage your preferences in detail.",
                    "banner_title": "Manage Your Consent",
                }
            ],
        },
    )

    yield config
    for translation in config.translations:
        for history in translation.histories:
            history.delete(db)
        translation.delete(db)

    config.delete(db)


@pytest.fixture(scope="function")
def privacy_experience_overlay(
    db: Session, experience_config_banner_and_modal
) -> Generator:
    privacy_experience = PrivacyExperience.create(
        db=db,
        data={
            "region": PrivacyNoticeRegion.us_ca,
            "experience_config_id": experience_config_banner_and_modal.id,
        },
    )

    yield privacy_experience
    privacy_experience.delete(db)


@pytest.fixture(scope="function")
def privacy_experience_privacy_center_france(
    db: Session, experience_config_privacy_center
) -> Generator:
    privacy_experience = PrivacyExperience.create(
        db=db,
        data={
            "region": PrivacyNoticeRegion.fr,
            "experience_config_id": experience_config_privacy_center.id,
        },
    )

    yield privacy_experience
    privacy_experience.delete(db)


@pytest.fixture(scope="function")
def privacy_experience_france_tcf_overlay(
    db: Session, experience_config_tcf_overlay
) -> Generator:
    privacy_experience = PrivacyExperience.create(
        db=db,
        data={
            "region": PrivacyNoticeRegion.fr,
            "experience_config_id": experience_config_tcf_overlay.id,
        },
    )

    yield privacy_experience

    privacy_experience.delete(db)


@pytest.fixture(scope="function")
def privacy_experience_france_overlay(
    db: Session, experience_config_banner_and_modal
) -> Generator:
    privacy_experience = PrivacyExperience.create(
        db=db,
        data={
            "region": PrivacyNoticeRegion.fr,
            "experience_config_id": experience_config_banner_and_modal.id,
        },
    )

    yield privacy_experience
    privacy_experience.delete(db)
