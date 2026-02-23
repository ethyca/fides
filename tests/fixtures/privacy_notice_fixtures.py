from typing import Generator

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

from fides.api.models.asset import Asset
from fides.api.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    PrivacyNotice,
    PrivacyNoticeTemplate,
)


@pytest.fixture(scope="function")
def privacy_notice_targeted_advertising(db: Session) -> Generator:
    """
    Privacy notice fixture for targeted advertising use cases.

    Creates a privacy notice with targeted advertising data uses that can be used
    to test matching with various cookie assets.
    """
    template = PrivacyNoticeTemplate.create(
        db,
        check_name=False,
        data={
            "name": "targeted advertising notice",
            "notice_key": "targeted_advertising_notice_1",
            "consent_mechanism": ConsentMechanism.opt_out,
            "data_uses": [
                "marketing.advertising.first_party.targeted",
                "marketing.advertising.third_party.targeted",
            ],
            "enforcement_level": EnforcementLevel.system_wide,
            "translations": [
                {
                    "language": "en",
                    "title": "Targeted Advertising Notice",
                    "description": "Notice for targeted advertising",
                }
            ],
        },
    )
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "targeted advertising notice",
            "notice_key": "targeted_advertising_notice_1",
            "consent_mechanism": ConsentMechanism.opt_out,
            "data_uses": [
                "marketing.advertising.first_party.targeted",
                "marketing.advertising.third_party.targeted",
            ],
            "enforcement_level": EnforcementLevel.system_wide,
            "origin": template.id,
            "translations": [
                {
                    "language": "en",
                    "title": "Targeted Advertising Notice",
                    "description": "Notice for targeted advertising",
                }
            ],
        },
    )

    yield privacy_notice

    # Clean up translations and histories
    for translation in privacy_notice.translations:
        for history in translation.histories:
            history.delete(db)
        translation.delete(db)
    privacy_notice.delete(db)
    template.delete(db)


@pytest.fixture(scope="function")
def multi_data_use_cookie_asset(db: Session, system) -> Generator:
    """
    Asset that mimics a real-world cookie with multiple data uses.
    """
    asset = Asset(
        name="_gcl_au",
        asset_type="Cookie",
        domain="*",
        system_id=system.id,
        data_uses=[
            "marketing.advertising.first_party.contextual",
            "marketing.advertising.negative_targeting",
            "analytics.reporting.campaign_insights",
            "marketing.advertising.first_party.targeted",  # Should match targeted advertising notices
            "analytics.reporting.ad_performance",
            "functional.service.improve",
            "marketing.advertising.third_party.targeted",  # Should match targeted advertising notices
            "marketing.advertising.profiling",
            "marketing.advertising.frequency_capping",
            "functional.storage",
        ],
        locations=[],
        parent=[],
        consent_status="unknown",
        page=[],
    )
    asset.save(db)

    yield asset

    # Clean up
    try:
        asset.delete(db)
    except ObjectDeletedError:
        # Skip if already deleted
        pass


@pytest.fixture(scope="function")
def privacy_notice_fun_data_use(db: Session) -> Generator:
    """
    Privacy notice fixture for testing substring matching edge cases.

    Creates a privacy notice with 'fun' data use to test against 'funding' assets.
    """
    template = PrivacyNoticeTemplate.create(
        db,
        check_name=False,
        data={
            "name": "fun activities notice",
            "notice_key": "fun_activities_notice_1",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["fun"],
            "enforcement_level": EnforcementLevel.system_wide,
            "translations": [
                {
                    "language": "en",
                    "title": "Fun Activities Notice",
                    "description": "Notice for fun activities",
                }
            ],
        },
    )
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "fun activities notice",
            "notice_key": "fun_activities_notice_1",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["fun"],
            "enforcement_level": EnforcementLevel.system_wide,
            "origin": template.id,
            "translations": [
                {
                    "language": "en",
                    "title": "Fun Activities Notice",
                    "description": "Notice for fun activities",
                }
            ],
        },
    )

    yield privacy_notice

    # Clean up
    for translation in privacy_notice.translations:
        for history in translation.histories:
            history.delete(db)
        translation.delete(db)
    privacy_notice.delete(db)
    template.delete(db)


@pytest.fixture(scope="function")
def privacy_notice_empty_data_uses(db: Session) -> Generator:
    """
    Privacy notice fixture with no data uses for testing edge cases.

    Creates a privacy notice with empty data uses list to test that it returns
    no cookies regardless of what cookie assets exist.
    """
    template = PrivacyNoticeTemplate.create(
        db,
        check_name=False,
        data={
            "name": "Empty Notice",
            "notice_key": "empty_notice_1",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": [],  # Empty data uses
            "enforcement_level": EnforcementLevel.system_wide,
            "translations": [
                {
                    "language": "en",
                    "title": "Empty Notice",
                    "description": "This notice has no data uses.",
                }
            ],
        },
    )
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "Empty Notice",
            "notice_key": "empty_notice_1",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": [],  # Empty data uses
            "enforcement_level": EnforcementLevel.system_wide,
            "origin": template.id,
            "translations": [
                {
                    "language": "en",
                    "title": "Empty Notice",
                    "description": "This notice has no data uses.",
                }
            ],
        },
    )

    yield privacy_notice

    # Clean up
    for translation in privacy_notice.translations:
        for history in translation.histories:
            history.delete(db)
        translation.delete(db)
    privacy_notice.delete(db)
    template.delete(db)


@pytest.fixture(scope="function")
def privacy_notice_2(db: Session) -> Generator:
    template = PrivacyNoticeTemplate.create(
        db,
        check_name=False,
        data={
            "name": "example privacy notice 2",
            "notice_key": "example_privacy_notice_2",
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
        },
    )
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "example privacy notice 2",
            "notice_key": "example_privacy_notice_2",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["marketing.advertising", "third_party_sharing"],
            "enforcement_level": EnforcementLevel.system_wide,
            "origin": template.id,
            "translations": [
                {
                    "language": "en",
                    "title": "Example privacy notice",
                    "description": "user&#x27;s description &lt;script /&gt;",
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
def privacy_notice(db: Session) -> Generator:
    template = PrivacyNoticeTemplate.create(
        db,
        check_name=False,
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
        },
    )
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "example privacy notice",
            "notice_key": "example_privacy_notice_1",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["marketing.advertising", "third_party_sharing"],
            "enforcement_level": EnforcementLevel.system_wide,
            "origin": template.id,
            "translations": [
                {
                    "language": "en",
                    "title": "Example privacy notice",
                    "description": "user&#x27;s description &lt;script /&gt;",
                }
            ],
        },
    )

    # Create cookie assets
    cookie_assets = [
        Asset(
            name="test_cookie",
            asset_type="Cookie",
            data_uses=["marketing.advertising"],
        ),
        Asset(
            name="test_cookie_2",
            asset_type="Cookie",
            data_uses=["third_party_sharing.disclosure"],  # a not matching data use
        ),
        Asset(
            name="test_cookie_3",
            asset_type="Cookie",
            data_uses=["test.third_party_sharing.cookie"],  # should not match either
        ),
    ]
    for cookie_asset in cookie_assets:
        cookie_asset.save(db)

    yield privacy_notice

    # Clean up cookie assets first
    for cookie in cookie_assets:
        try:
            cookie.delete(db)
        except ObjectDeletedError:
            # Skip if already deleted
            pass

    # Then clean up translations and histories
    for translation in privacy_notice.translations:
        for history in translation.histories:
            history.delete(db)
        translation.delete(db)
    privacy_notice.delete(db)


@pytest.fixture(scope="function")
def privacy_notice_us_ca_provide(db: Session) -> Generator:
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "example privacy notice us_ca provide",
            "notice_key": "example_privacy_notice_us_ca_provide",
            # no origin on this privacy notice to help
            # cover edge cases due to column nullability
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["essential"],
            "enforcement_level": EnforcementLevel.system_wide,
            "translations": [
                {
                    "language": "en",
                    "title": "example privacy notice us_ca provide",
                }
            ],
        },
    )

    yield privacy_notice


@pytest.fixture(scope="function")
def privacy_notice_us_co_third_party_sharing(db: Session) -> Generator:
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "example privacy notice us_co third_party_sharing",
            "notice_key": "example_privacy_notice_us_co_third_party_sharing",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["third_party_sharing"],
            "enforcement_level": EnforcementLevel.system_wide,
            "translations": [
                {
                    "language": "en",
                    "title": "example privacy notice us_co third_party_sharing",
                    "description": "a sample privacy notice configuration",
                }
            ],
        },
    )

    yield privacy_notice


@pytest.fixture(scope="function")
def privacy_notice_us_co_provide_service_operations(db: Session) -> Generator:
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "example privacy notice us_co provide.service.operations",
            "notice_key": "example_privacy_notice_us_co_provide.service.operations",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["essential.service.operations"],
            "enforcement_level": EnforcementLevel.system_wide,
            "translations": [
                {
                    "language": "en",
                    "title": "example privacy notice us_co provide.service.operations",
                    "description": "a sample privacy notice configuration",
                }
            ],
        },
    )

    yield privacy_notice


@pytest.fixture(scope="function")
def privacy_notice_fr_provide_service_frontend_only(db: Session) -> Generator:
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "example privacy notice us_co provide.service.operations",
            "notice_key": "example_privacy_notice_us_co_provide.service.operations",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["essential.service"],
            "enforcement_level": EnforcementLevel.frontend,
            "translations": [
                {
                    "language": "en",
                    "title": "example privacy notice us_co provide.service.operations",
                    "description": "a sample privacy notice configuration",
                }
            ],
        },
    )

    yield privacy_notice


@pytest.fixture(scope="function")
def privacy_notice_eu_cy_provide_service_frontend_only(db: Session) -> Generator:
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "example privacy notice eu_cy provide.service.operations",
            "notice_key": "example_privacy_notice_eu_cy_provide.service.operations",
            "consent_mechanism": ConsentMechanism.opt_out,
            "data_uses": ["essential.service"],
            "enforcement_level": EnforcementLevel.frontend,
            "translations": [
                {
                    "language": "en",
                    "title": "example privacy notice eu_cy provide.service.operations",
                    "description": "a sample privacy notice configuration",
                }
            ],
        },
    )

    yield privacy_notice


@pytest.fixture(scope="function")
def privacy_notice_france(db: Session) -> Generator:
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "example privacy notice",
            "notice_key": "example_privacy_notice",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["marketing.advertising", "third_party_sharing"],
            "enforcement_level": EnforcementLevel.system_wide,
            "translations": [
                {
                    "language": "en",
                    "title": "example privacy notice",
                    "description": "user description",
                }
            ],
        },
    )

    yield privacy_notice
