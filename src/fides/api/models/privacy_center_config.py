from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict

from fides.api.db.base_class import Base

default_privacy_center_config = {
    "title": "Take control of your data",
    "description": "When you use our services, you’re trusting us with your information. We understand this is a big responsibility and work hard to protect your information and put you in control.",
    "description_subtext": [],
    "addendum": [],
    "logo_path": "/logo.svg",
    "logo_url": "https://fid.es",
    "privacy_policy_url": "https://fid.es/privacy",
    "privacy_policy_url_text": "Privacy Policy",
    "favicon_path": "/favicon.ico",
    "actions": [
        {
            "policy_key": "default_access_policy",
            "icon_path": "/download.svg",
            "title": "Access your data",
            "description": "We will provide you a report of all your personal data.",
            "description_subtext": [],
            "identity_inputs": {"email": "required"},
            "confirmButtonText": "Continue",
            "cancelButtonText": "Cancel",
        },
        {
            "policy_key": "default_erasure_policy",
            "icon_path": "/delete.svg",
            "title": "Erase your data",
            "description": "We will erase all of your personal data. This action cannot be undone.",
            "description_subtext": [],
            "identity_inputs": {"email": "required"},
            "confirmButtonText": "Continue",
            "cancelButtonText": "Cancel",
        },
    ],
    "includeConsent": True,
    "consent": {
        "button": {
            "description": "Manage your consent preferences, including the option to select 'Do Not Sell or Share My Personal Information'.",
            "description_subtext": [
                "In order to opt-out of certain consent preferences, we may need to identify your account via your email address. This is optional."
            ],
            "icon_path": "/consent.svg",
            "identity_inputs": {"email": "optional"},
            "title": "Manage your consent",
            "modalTitle": "Manage your consent",
            "confirmButtonText": "Continue",
            "cancelButtonText": "Cancel",
        },
        "page": {
            "consentOptions": [
                {
                    "fidesDataUseKey": "marketing.advertising",
                    "name": "Data Sales or Sharing",
                    "description": "We may use some of your personal information for behavioral advertising purposes, which may be interpreted as 'Data Sales' or 'Data Sharing' under regulations such as CCPA, CPRA, VCDPA, etc.",
                    "url": "https://example.com/privacy#data-sales",
                    "default": {"value": True, "globalPrivacyControl": False},
                    "highlight": False,
                    "cookieKeys": ["data_sales"],
                    "executable": False,
                },
                {
                    "fidesDataUseKey": "marketing.advertising.first_party",
                    "name": "Email Marketing",
                    "description": "We may use some of your personal information to contact you about our products & services.",
                    "url": "https://example.com/privacy#email-marketing",
                    "default": {"value": True, "globalPrivacyControl": False},
                    "highlight": False,
                    "cookieKeys": ["tracking"],
                    "executable": False,
                },
                {
                    "fidesDataUseKey": "functional",
                    "name": "Product Analytics",
                    "description": "We may use some of your personal information to collect analytics about how you use our products & services.",
                    "url": "https://example.com/privacy#analytics",
                    "default": True,
                    "highlight": False,
                    "cookieKeys": ["analytics"],
                    "executable": False,
                },
            ],
            "description": "Manage your consent preferences, including the option to select 'Do Not Sell or Share My Personal Information'.",
            "description_subtext": [
                "When you use our services, you're trusting us with your information. We understand this is a big responsibility and work hard to protect your information and put you in control."
            ],
            "policy_key": "default_consent_policy",
            "title": "Manage your consent",
        },
    },
}


class PrivacyCenterConfig(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "plus_privacy_center_config"

    config = Column(
        MutableDict.as_mutable(JSONB),
        nullable=False,
    )
