# pylint: disable=missing-docstring, redefined-outer-name
from typing import Generator, List

import pytest
from fideslang.models import (
    ContactDetails,
    DataSubject,
    DataSubjectRights,
    DataUse,
    Organization,
)

from fidesctl.ctl.core import audit


@pytest.fixture
def test_default_organization() -> Generator:
    yield [Organization(fides_key="default_organization")]


@pytest.fixture
def test_rich_organization() -> Generator:
    test_contact = ContactDetails(name="test")
    yield [
        Organization(
            fides_key="default_organization",
            controller=test_contact,
            data_protection_officer=test_contact,
            representative=test_contact,
            security_policy="http://sample.org/",
        )
    ]


@pytest.fixture
def test_basic_data_use() -> Generator:
    yield [DataUse(fides_key="test_data_use")]


@pytest.fixture
def test_rich_data_use() -> Generator:
    yield [
        DataUse(
            fides_key="test_data_use",
            recipients=["test"],
            legal_basis="Consent",
            special_category="Consent",
        )
    ]


@pytest.fixture
def test_basic_data_subject() -> Generator:
    yield [DataSubject(fides_key="test_data_subject")]


@pytest.fixture
def test_rich_data_subject() -> Generator:
    data_subject_rights = DataSubjectRights(strategy="ALL", values=None)
    yield [
        DataSubject(
            fides_key="test_data_subject",
            rights=data_subject_rights,
            automated_decisions_or_profiling=False,
        )
    ]


@pytest.mark.unit
def test_basic_organization_fails_audit(
    test_default_organization: List[Organization],
) -> None:
    audit_findings = audit.audit_organization_attributes(test_default_organization[0])
    assert audit_findings > 0


@pytest.mark.unit
def test_rich_organization_passes_audit(
    test_rich_organization: List[Organization],
) -> None:
    audit_findings = audit.audit_organization_attributes(test_rich_organization[0])
    assert audit_findings == 0


@pytest.mark.unit
def test_basic_data_use_fails_audit(
    test_basic_data_use: List[DataUse],
) -> None:
    audit_findings = audit.audit_data_use_attributes(
        test_basic_data_use[0], "test_system_name"
    )
    assert audit_findings > 0


@pytest.mark.unit
def test_rich_data_use_passes_audit(
    test_rich_data_use: List[DataUse],
) -> None:
    audit_findings = audit.audit_data_use_attributes(
        test_rich_data_use[0], "test_system_name"
    )
    assert audit_findings == 0


@pytest.mark.unit
def test_basic_data_subject_fails_audit(
    test_basic_data_subject: List[DataSubject],
) -> None:
    audit_findings = audit.audit_data_subject_attributes(
        test_basic_data_subject[0], "test_system_name"
    )
    assert audit_findings > 0


@pytest.mark.unit
def test_rich_data_subject_passes_audit(
    test_rich_data_subject: List[DataSubject],
) -> None:
    audit_findings = audit.audit_data_subject_attributes(
        test_rich_data_subject[0], "test_system_name"
    )
    assert audit_findings == 0
