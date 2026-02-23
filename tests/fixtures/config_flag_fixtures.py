from pathlib import Path

import pytest
from loguru import logger

from fides.api.models.application_config import ApplicationConfig
from fides.api.schemas.messaging.messaging import MessagingServiceType
from fides.api.tasks import celery_app
from fides.config import get_config
from fides.config.config_proxy import ConfigProxy

ROOT_PATH = Path().absolute()
CONFIG = get_config()
TEST_CONFIG_PATH = "tests/cli/test_config.toml"
TEST_INVALID_CONFIG_PATH = "tests/cli/test_invalid_config.toml"
TEST_DEPRECATED_CONFIG_PATH = "tests/cli/test_deprecated_config.toml"


@pytest.fixture(scope="session")
def config():
    CONFIG.test_mode = True
    yield CONFIG


@pytest.fixture(scope="function")
def enable_tcf(config):
    assert config.test_mode
    config.consent.tcf_enabled = True
    yield config
    config.consent.tcf_enabled = False


@pytest.fixture(scope="function")
def enable_celery_worker(config):
    """This doesn't actually spin up a worker container"""
    celery_app.conf["task_always_eager"] = False
    yield config
    celery_app.conf["task_always_eager"] = True


@pytest.fixture(scope="function")
def enable_ac(config):
    assert config.test_mode
    config.consent.ac_enabled = True
    yield config
    config.consent.ac_enabled = False


@pytest.fixture(scope="function")
def enable_override_vendor_purposes(config, db):
    assert config.test_mode
    config.consent.override_vendor_purposes = True
    ApplicationConfig.create_or_update(
        db,
        data={"config_set": {"consent": {"override_vendor_purposes": True}}},
    )
    yield config
    config.consent.override_vendor_purposes = False
    ApplicationConfig.create_or_update(
        db,
        data={"config_set": {"consent": {"override_vendor_purposes": False}}},
    )


@pytest.fixture(scope="function")
def enable_override_vendor_purposes_api_set(db):
    """Enable override vendor purposes via api_set setting, not via traditional app config"""
    ApplicationConfig.create_or_update(
        db,
        data={"api_set": {"consent": {"override_vendor_purposes": True}}},
    )
    yield
    # reset back to false on teardown
    ApplicationConfig.create_or_update(
        db,
        data={"api_set": {"consent": {"override_vendor_purposes": False}}},
    )


@pytest.fixture
def loguru_caplog(caplog):
    handler_id = logger.add(caplog.handler, format="{message} | {extra}")
    yield caplog
    logger.remove(handler_id)


@pytest.fixture
def fides_toml_path():
    yield ROOT_PATH / ".fides" / "fides.toml"


@pytest.fixture(scope="function", autouse=True)
def clear_get_config_cache() -> None:
    get_config.cache_clear()


@pytest.fixture(scope="session")
def test_config_path():
    yield TEST_CONFIG_PATH


@pytest.fixture(scope="session")
def test_deprecated_config_path():
    yield TEST_DEPRECATED_CONFIG_PATH


@pytest.fixture(scope="session")
def test_invalid_config_path():
    """
    This config file contains url/connection strings that are invalid.

    This ensures that the CLI isn't calling out to those resources
    directly during certain tests.
    """
    yield TEST_INVALID_CONFIG_PATH


@pytest.fixture(scope="session")
def test_config(test_config_path: str):
    yield get_config(test_config_path)


@pytest.fixture
def test_config_dev_mode_disabled():
    original_value = CONFIG.dev_mode
    CONFIG.dev_mode = False
    yield CONFIG
    CONFIG.dev_mode = original_value


@pytest.fixture
def automatically_approved(db):
    """Do not require manual request approval"""
    original_value = CONFIG.execution.require_manual_request_approval
    CONFIG.execution.require_manual_request_approval = False
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.execution.require_manual_request_approval = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture
def require_manual_request_approval(db):
    """Require manual request approval"""
    original_value = CONFIG.execution.require_manual_request_approval
    CONFIG.execution.require_manual_request_approval = True
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.execution.require_manual_request_approval = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture
def subject_identity_verification_required(db):
    """Enable identity verification."""
    original_value = CONFIG.execution.subject_identity_verification_required
    CONFIG.execution.subject_identity_verification_required = True
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.execution.subject_identity_verification_required = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture(scope="function")
def subject_identity_verification_not_required(db):
    """Disable identity verification for most tests unless overridden"""
    original_value = CONFIG.execution.subject_identity_verification_required
    CONFIG.execution.subject_identity_verification_required = False
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()
    yield
    CONFIG.execution.subject_identity_verification_required = original_value
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()


@pytest.fixture(scope="function")
def disable_consent_identity_verification(db):
    """Fixture to set disable_consent_identity_verification for tests"""
    original_value = CONFIG.execution.disable_consent_identity_verification
    CONFIG.execution.disable_consent_identity_verification = True
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.execution.disable_consent_identity_verification = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture(scope="function")
def privacy_request_complete_email_notification_disabled(db):
    """Disable request completion email for most tests unless overridden"""
    original_value = CONFIG.notifications.send_request_completion_notification
    CONFIG.notifications.send_request_completion_notification = False
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()
    yield
    CONFIG.notifications.send_request_completion_notification = original_value
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()


@pytest.fixture(scope="function")
def privacy_request_receipt_notification_disabled(db):
    """Disable request receipt notification for most tests unless overridden"""
    original_value = CONFIG.notifications.send_request_receipt_notification
    CONFIG.notifications.send_request_receipt_notification = False
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()
    yield
    CONFIG.notifications.send_request_receipt_notification = original_value
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()


@pytest.fixture(scope="function")
def privacy_request_review_notification_disabled(db):
    """Disable request review notification for most tests unless overridden"""
    original_value = CONFIG.notifications.send_request_review_notification
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()
    CONFIG.notifications.send_request_review_notification = False
    yield
    CONFIG.notifications.send_request_review_notification = original_value
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()


@pytest.fixture(scope="function")
def set_notification_service_type_to_mailgun(db):
    """Set default notification service type"""
    original_value = CONFIG.notifications.notification_service_type
    CONFIG.notifications.notification_service_type = MessagingServiceType.mailgun.value
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()
    yield
    CONFIG.notifications.notification_service_type = original_value
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()


@pytest.fixture(scope="function")
def set_notification_service_type_to_none(db):
    """Overrides autouse fixture to remove default notification service type"""
    original_value = CONFIG.notifications.notification_service_type
    CONFIG.notifications.notification_service_type = None
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.notifications.notification_service_type = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture(scope="function")
def set_notification_service_type_to_twilio_email(db):
    """Overrides autouse fixture to set notification service type to twilio email"""
    original_value = CONFIG.notifications.notification_service_type
    CONFIG.notifications.notification_service_type = (
        MessagingServiceType.twilio_email.value
    )
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.notifications.notification_service_type = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture(scope="function")
def set_notification_service_type_to_twilio_text(db):
    """Overrides autouse fixture to set notification service type to twilio text"""
    original_value = CONFIG.notifications.notification_service_type
    CONFIG.notifications.notification_service_type = (
        MessagingServiceType.twilio_text.value
    )
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.notifications.notification_service_type = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture(scope="function")
def set_property_specific_messaging_enabled(db):
    """Overrides autouse fixture to enable property specific messaging"""
    original_value = CONFIG.notifications.enable_property_specific_messaging
    CONFIG.notifications.enable_property_specific_messaging = True
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.notifications.enable_property_specific_messaging = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture(scope="function")
def set_property_specific_messaging_disabled(db):
    """Disable property specific messaging for all tests unless overridden"""
    original_value = CONFIG.notifications.enable_property_specific_messaging
    CONFIG.notifications.enable_property_specific_messaging = False
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.notifications.enable_property_specific_messaging = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture(scope="session")
def config_proxy(db):
    return ConfigProxy(db)
