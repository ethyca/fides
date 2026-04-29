"""Regression tests pinning extras behaviour on PrivacyRequestOption.

The form builder relies on round-tripping `_form_builder_spec` through the
schema. If extras are forbidden or silently dropped, the builder loses state
on save.
"""
from fides.api.schemas.privacy_center_config import PrivacyRequestOption


def test_privacy_request_option_preserves_unknown_extras() -> None:
    payload = {
        "icon_path": "/icon.svg",
        "title": "Access My Data",
        "description": "Request a copy of your data.",
        "_form_builder_spec": {
            "version": 1,
            "spec": {"root": "form", "elements": {}},
            "updated_at": "2026-04-28T15:04:05Z",
            "updated_by": "user-123",
        },
    }

    parsed = PrivacyRequestOption.model_validate(payload)
    dumped = parsed.model_dump(by_alias=True)

    assert dumped["_form_builder_spec"]["version"] == 1
    assert dumped["_form_builder_spec"]["spec"] == {
        "root": "form",
        "elements": {},
    }
    assert dumped["_form_builder_spec"]["updated_by"] == "user-123"
