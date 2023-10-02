from __future__ import annotations

import re
from collections import defaultdict
from enum import Enum
from html import unescape
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type, Union

from fideslang.validation import FidesKey
from sqlalchemy import Boolean, Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import Float, ForeignKey, String, or_
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Session, relationship
from sqlalchemy.util import hybridproperty

from fides.api.common_exceptions import ValidationError
from fides.api.db.base_class import Base, FidesBase
from fides.api.models.sql_models import (  # type: ignore[attr-defined]
    Cookies,
    PrivacyDeclaration,
    System,
)


class UserConsentPreference(Enum):
    opt_in = "opt_in"  # The user wants to opt in to the notice
    opt_out = "opt_out"  # The user wants to opt out of the notice
    acknowledge = "acknowledge"  # The user has acknowledged this notice


# Enum defined using functional API so we can use regions like "is"
PrivacyNoticeRegion = Enum(
    "PrivacyNoticeRegion",
    [
        ("us", "us"),  # united states
        ("us_al", "us_al"),  # alabama
        ("us_ak", "us_ak"),  # alaska
        ("us_az", "us_az"),  # arizona
        ("us_ar", "us_ar"),  # arkansas
        ("us_ca", "us_ca"),  # california
        ("us_co", "us_co"),  # colorado
        ("us_ct", "us_ct"),  # connecticut
        ("us_de", "us_de"),  # delaware
        ("us_fl", "us_fl"),  # florida
        ("us_ga", "us_ga"),  # georgia
        ("us_hi", "us_hi"),  # hawaii
        ("us_id", "us_id"),  # idaho
        ("us_il", "us_il"),  # illinois
        ("us_in", "us_in"),  # indiana
        ("us_ia", "us_ia"),  # iowa
        ("us_ks", "us_ks"),  # kansas
        ("us_ky", "us_ky"),  # kentucky
        ("us_la", "us_la"),  # louisiana
        ("us_me", "us_me"),  # maine
        ("us_md", "us_md"),  # maryland
        ("us_ma", "us_ma"),  # massachusetts
        ("us_mi", "us_mi"),  # michigan
        ("us_mn", "us_mn"),  # minnesota
        ("us_ms", "us_ms"),  # mississippi
        ("us_mo", "us_mo"),  # missouri
        ("us_mt", "us_mt"),  # montana
        ("us_ne", "us_ne"),  # nebraska
        ("us_nv", "us_nv"),  # nevada
        ("us_nh", "us_nh"),  # new hampshire
        ("us_nj", "us_nj"),  # new jersey
        ("us_nm", "us_nm"),  # new mexico
        ("us_ny", "us_ny"),  # new york
        ("us_nc", "us_nc"),  # north carolina
        ("us_nd", "us_nd"),  # north dakota
        ("us_oh", "us_oh"),  # ohio
        ("us_ok", "us_ok"),  # oklahoma
        ("us_or", "us_or"),  # oregon
        ("us_pa", "us_pa"),  # pennsylvania
        ("us_ri", "us_ri"),  # rhode island
        ("us_sc", "us_sc"),  # south carolina
        ("us_sd", "us_sd"),  # south dakota
        ("us_tn", "us_tn"),  # tennessee
        ("us_tx", "us_tx"),  # texas
        ("us_ut", "us_ut"),  # utah
        ("us_vt", "us_vt"),  # vermont
        ("us_va", "us_va"),  # virginia
        ("us_wa", "us_wa"),  # washington
        ("us_wv", "us_wv"),  # west virginia
        ("us_wi", "us_wi"),  # wisconsin
        ("us_wy", "us_wy"),  # wyoming
        ("eea", "eea"),  # european economic area
        ("be", "be"),  # belgium
        ("bg", "bg"),  # bulgaria
        ("cz", "cz"),  # czechia
        ("dk", "dk"),  # denmark
        ("de", "de"),  # germany
        ("ee", "ee"),  # estonia
        ("ie", "ie"),  # ireland
        ("gr", "gr"),  # greece
        ("es", "es"),  # spain
        ("fr", "fr"),  # france
        ("hr", "hr"),  # croatia
        ("it", "it"),  # italy
        ("cy", "cy"),  # cyprus
        ("lv", "lv"),  # latvia
        ("lt", "lt"),  # lithuania
        ("lu", "lu"),  # luxembourg
        ("hu", "hu"),  # hungary
        ("mt", "mt"),  # malta
        ("nl", "nl"),  # netherlands
        ("at", "at"),  # austria
        ("pl", "pl"),  # poland
        ("pt", "pt"),  # portugal
        ("ro", "ro"),  # romania
        ("si", "si"),  # slovenia
        ("sk", "sk"),  # slovakia
        ("fi", "fi"),  # finland
        ("se", "se"),  # sweden
        ("gb_eng", "gb_eng"),  # england
        ("gb_sct", "gb_sct"),  # scotland
        ("gb_wls", "gb_wls"),  # wales
        ("gb_nir", "gb_nir"),  # northern ireland
        ("is", "is"),  # iceland
        ("no", "no"),  # norway
        ("li", "li"),  # liechtenstein
        ("ca", "ca"),  # canada
        ("ca_ab", "ca_ab"),  # alberta
        ("ca_bc", "ca_bc"),  # british columbia
        ("ca_mb", "ca_mb"),  # manitoba
        ("ca_nb", "ca_nb"),  # new brunswick
        ("ca_nl", "ca_nl"),  # newfoundland and labrador
        ("ca_ns", "ca_ns"),  # nova scotia
        ("ca_on", "ca_on"),  # ontario
        ("ca_pe", "ca_pe"),  # prince edward island
        ("ca_qc", "ca_qc"),  # quebec
        ("ca_sk", "ca_sk"),  # saskatchewan
        ("ca_nt", "ca_nt"),  # northwest territories
        ("ca_nu", "ca_nu"),  # nunavut
        ("ca_yt", "ca_yt"),  # yukon
    ],
)


class ConsentMechanism(Enum):
    opt_in = "opt_in"
    opt_out = "opt_out"
    notice_only = "notice_only"


class EnforcementLevel(Enum):
    """
    Enum is not formalized in the DB because it may be subject to frequent change
    """

    frontend = "frontend"
    system_wide = "system_wide"
    not_applicable = "not_applicable"


class PrivacyNoticeBase:
    """
    This class contains the common fields between PrivacyNoticeTemplate, PrivacyNotice, and PrivacyNoticeHistory
    """

    name = Column(String, nullable=False)
    description = Column(String)  # User-facing description
    internal_description = Column(String)  # Visible to internal users only
    regions = Column(
        ARRAY(EnumColumn(PrivacyNoticeRegion, native_enum=False)),
        index=True,
        nullable=False,
    )
    consent_mechanism = Column(EnumColumn(ConsentMechanism), nullable=False)
    data_uses = Column(
        ARRAY(String), nullable=False
    )  # a list of `fides_key`s of `DataUse` records
    enforcement_level = Column(EnumColumn(EnforcementLevel), nullable=False)
    disabled = Column(Boolean, nullable=False, default=False)
    has_gpc_flag = Column(Boolean, nullable=False, default=False)
    displayed_in_privacy_center = Column(Boolean, nullable=False, default=False)
    displayed_in_overlay = Column(Boolean, nullable=False, default=False)
    displayed_in_api = Column(Boolean, nullable=False, default=False)
    notice_key = Column(String, nullable=False)

    # Attribute that can be temporarily cached as the result of "get_related_privacy_notices"
    # for a given user, for surfacing CurrentPrivacyPreferences for the user.
    current_preference: Optional[str] = None
    outdated_preference: Optional[str] = None
    # Attributes that can be temporarily cached on the notice to see if the most
    # recent version or a previous version of a notice have ever been served to the user
    current_served: Optional[bool] = None
    outdated_served: Optional[bool] = None

    def applies_to_system(self, system: System) -> bool:
        """Privacy Notice applies to System if a data use matches or the Privacy Notice
        Data Use is a parent of a System Data Use
        """
        for system_data_use in System.get_data_uses([system], include_parents=True):
            for privacy_notice_data_use in self.data_uses or []:
                if system_data_use == privacy_notice_data_use:
                    return True
        return False

    @classmethod
    def generate_notice_key(cls, name: Optional[str]) -> FidesKey:
        """Generate a notice key from a notice name"""
        if not isinstance(name, str):
            raise Exception("Privacy notice keys must be generated from a string.")
        notice_key: str = re.sub(r"\s+", "_", name.lower().strip())
        return FidesKey(FidesKey.validate(notice_key))

    def dry_update(self, *, data: dict[str, Any]) -> FidesBase:
        """
        A utility method to get an updated object without saving it to the db.

        This is used to see what an object update would look like, in memory,
        without actually persisting the update to the db
        """
        # Update our attributes with values in data
        cloned_attributes = self.__dict__.copy()
        for key, val in data.items():
            cloned_attributes[key] = val

        # remove protected fields from the cloned dict
        cloned_attributes.pop("_sa_instance_state")

        # create a new object with the updated attribute data to keep this
        # ORM object (i.e., `self`) pristine
        return PrivacyNotice(**cloned_attributes)


class PrivacyNoticeTemplate(PrivacyNoticeBase, Base):
    """
    This table contains the out-of-the-box Privacy Notices that are shipped with Fides
    """


class PrivacyNotice(PrivacyNoticeBase, Base):
    """
    A notice set up by a system administrator that an end user (i.e., data subject)
    accepts or rejects to indicate their consent for particular data uses
    """

    origin = Column(
        String, ForeignKey(PrivacyNoticeTemplate.id_field_path), nullable=True
    )  # pointer back to the PrivacyNoticeTemplate
    version = Column(Float, nullable=False, default=1.0)

    histories = relationship(
        "PrivacyNoticeHistory", backref="privacy_notice", lazy="dynamic"
    )

    @hybridproperty
    def privacy_notice_history_id(self) -> Optional[str]:
        """Convenience property that returns the historical privacy notice history id for the current version.

        Note that there are possibly many historical records for the given notice, this just returns the current
        corresponding historical record.
        """
        history: PrivacyNoticeHistory = self.histories.filter_by(  # type: ignore # pylint: disable=no-member
            version=self.version
        ).first()
        return history.id if history else None

    @hybridproperty
    def default_preference(self) -> UserConsentPreference:
        """Returns the user's default consent preference given the consent
        mechanism of this notice, or "what is granted to the user"

        For example, if a notice has an opt in consent mechanism, this means
        that they should be granted the opportunity to opt in, but by
        default, they *should be opted out*
        """
        if self.consent_mechanism == ConsentMechanism.opt_in:
            return UserConsentPreference.opt_out  # Intentional
        if self.consent_mechanism == ConsentMechanism.opt_out:
            return UserConsentPreference.opt_in  # Intentional
        if self.consent_mechanism == ConsentMechanism.notice_only:
            return UserConsentPreference.acknowledge

        raise Exception("Invalid notice consent mechanism.")

    @property
    def cookies(self) -> List[Cookies]:
        """Return relevant cookie names (via the data use)"""
        db = Session.object_session(self)
        return (
            db.query(Cookies)
            .join(
                PrivacyDeclaration,
                PrivacyDeclaration.id == Cookies.privacy_declaration_id,
            )
            .filter(
                or_(
                    *[
                        PrivacyDeclaration.data_use.like(f"{notice_use}%")
                        for notice_use in self.data_uses
                    ]
                )
            )
        ).all()

    @property
    def systems_applicable(self) -> bool:
        """Return if any systems overlap with this notice's data uses"""
        db = Session.object_session(self)
        for system in db.query(System):
            if self.applies_to_system(system):
                return True
        return False

    @classmethod
    def create(
        cls: Type[PrivacyNotice],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> PrivacyNotice:
        created = super().create(db=db, data=data, check_name=check_name)

        # create the history after the initial object creation succeeds, to avoid
        # writing history if the creation fails and so that we can get the generated ID
        data.pop("id", None)
        history_data = {**data, "privacy_notice_id": created.id}
        PrivacyNoticeHistory.create(db, data=history_data, check_name=False)
        return created

    def update(self, db: Session, *, data: dict[str, Any]) -> PrivacyNotice:
        """
        Overrides the base update method to automatically bump the version of the
        PrivacyNotice record and also create a new PrivacyNoticeHistory entry
        """
        resource, updated = update_if_modified(self, db=db, data=data)

        if updated:
            history_data = create_historical_data_from_record(resource)
            history_data["privacy_notice_id"] = resource.id
            PrivacyNoticeHistory.create(db, data=history_data, check_name=False)

        return resource  # type: ignore[return-value]


PRIVACY_NOTICE_TYPE = Union[PrivacyNotice, PrivacyNoticeTemplate]


def check_conflicting_notice_keys(
    new_privacy_notices: Iterable[PRIVACY_NOTICE_TYPE],
    existing_privacy_notices: Iterable[Union[PRIVACY_NOTICE_TYPE]],
    ignore_disabled: bool = True,  # For PrivacyNoticeTemplates, set to False
) -> None:
    """
    Checks to see if new notice keys will conflict with any existing notice keys for a specific region
    """
    # Map regions to existing notice key, notice name
    notice_keys_by_region: Dict[
        PrivacyNoticeRegion, List[Tuple[str, str]]
    ] = defaultdict(list)
    for privacy_notice in existing_privacy_notices:
        if privacy_notice.disabled and ignore_disabled:
            continue
        for region in privacy_notice.regions:
            notice_keys_by_region[PrivacyNoticeRegion(region)].append(
                (privacy_notice.notice_key, privacy_notice.name)
            )

    for privacy_notice in new_privacy_notices:
        if privacy_notice.disabled and ignore_disabled:
            # Skip validation if the notice is disabled
            continue
        # check each of the incoming notice's regions
        for region in privacy_notice.regions:
            region_notice_keys = notice_keys_by_region[PrivacyNoticeRegion(region)]
            # check the incoming notice keys
            for notice_key, notice_name in region_notice_keys:
                if notice_key == privacy_notice.notice_key:
                    raise ValidationError(
                        message=f"Privacy Notice '{unescape(notice_name)}' has already assigned notice key '{notice_key}' to region '{region}'"
                    )
            # add the new notice key to our map
            region_notice_keys.append((privacy_notice.notice_key, privacy_notice.name))


def check_conflicting_data_uses(
    new_privacy_notices: Iterable[PRIVACY_NOTICE_TYPE],
    existing_privacy_notices: Iterable[Union[PRIVACY_NOTICE_TYPE]],
    ignore_disabled: bool = True,  # For PrivacyNoticeTemplates, set to False
) -> None:
    """
    Checks the provided lists of potential "new" (incoming) `PrivacyNotice` records
    and existing `PrivacyNotice` records for conflicts (i.e. overlaps) in DataUse specifications
    within `PrivacyNoticeRegion`s associated with the `PrivacyNotice` records.

    Checks are effectively performed between the new records and the existing records, as well as
    between the new records themselves.

    A `DataUse` conflict is considered not only an exact match in `DataUse` strings, but also a
    hierarchical overlap, e.g. `DataUse`s of `advertising` and `advertising.first_party` as well as
    `advertising` and `advertising.first_party.contextual` would both be considered conflicts
    if they occurred in `PrivacyNotice`s that are associated with the same `PrivacyNoticeRegion`.

    For templates, we don't want to ignore disabled data uses.
    """
    # first, we map the existing [region -> data use] associations based on the set of
    # existing notices.
    # this gives us a simple "lookup table" for region and data use conflicts in incoming notices
    uses_by_region: Dict[PrivacyNoticeRegion, List[Tuple[str, str]]] = defaultdict(list)
    for privacy_notice in existing_privacy_notices:
        if privacy_notice.disabled and ignore_disabled:
            continue
        for region in privacy_notice.regions:
            for data_use in privacy_notice.data_uses:
                uses_by_region[PrivacyNoticeRegion(region)].append(
                    (data_use, privacy_notice.name)
                )

    # now, validate the new (incoming) notices
    for privacy_notice in new_privacy_notices:
        if privacy_notice.disabled and ignore_disabled:
            # if the incoming notice is disabled, it skips validation
            continue
        # check each of the incoming notice's regions
        for region in privacy_notice.regions:
            region_uses = uses_by_region[PrivacyNoticeRegion(region)]
            # check each of the incoming notice's data uses
            for data_use in privacy_notice.data_uses:
                for existing_use, notice_name in region_uses:
                    # we need to check for hierarchical overlaps in _both_ directions
                    # i.e. whether the incoming DataUse is a parent _or_ a child of
                    # an existing DataUse
                    if new_data_use_conflicts_with_existing_use(existing_use, data_use):
                        raise ValidationError(
                            message=f"Privacy Notice '{unescape(notice_name)}' has already assigned data use '{existing_use}' to region '{region}'"
                        )
                # add the data use to our map, to effectively include it in validation against the
                # following incoming records
                region_uses.append((data_use, privacy_notice.name))


def new_data_use_conflicts_with_existing_use(existing_use: str, new_use: str) -> bool:
    """Data use check that prevents grandparent/parent/child, but allows siblings, aunt/child, etc.
    Check needs to happen in both directions.
    This assumes the supplied uses are on notices in the same region.
    """
    return existing_use.startswith(new_use) or new_use.startswith(existing_use)


class PrivacyNoticeHistory(PrivacyNoticeBase, Base):
    """
    An "audit table" tracking outdated versions of `PrivacyNotice` records whose
    "current" versions are stored in the `PrivacyNotice` table/model
    """

    origin = Column(
        String, ForeignKey(PrivacyNoticeTemplate.id_field_path), nullable=True
    )  # pointer back to the PrivacyNoticeTemplate
    version = Column(Float, nullable=False, default=1.0)

    privacy_notice_id = Column(
        String, ForeignKey(PrivacyNotice.id_field_path), nullable=False
    )

    def calculate_relevant_systems(self, db: Session) -> List[FidesKey]:
        """Method to cache the relevant systems at the time to store on PrivacyPreferenceHistory for record keeping

        A system is relevant if their data use is an exact match or a child of the notice's data use.
        """
        relevant_systems: List[FidesKey] = []
        for system in db.query(System):
            if self.applies_to_system(system):
                relevant_systems.append(system.fides_key)
                continue
        return relevant_systems


def update_if_modified(
    resource: Base, db: Session, *, data: dict[str, Any]
) -> Tuple[Base, bool]:
    """Update the resource and increment its version if applicable.

    Return the updated resource and whether it was modified (which determines if we should create
    a corresponding historical record).

    Currently used for PrivacyNotice, PrivacyExperience, and PrivacyExperienceConfig models.
    """
    # run through potential updates now
    for key, value in data.items():
        setattr(resource, key, value)

    if db.is_modified(resource):
        # on any update to a privacy experience record, its version must be incremented
        # version gets incremented by a full integer, i.e. 1.0 -> 2.0 -> 3.0
        resource.version = float(resource.version) + 1.0  # type: ignore
        resource.save(db)
        return resource, True

    return resource, False


def create_historical_data_from_record(resource: Base) -> Dict:
    """Prep data to be saved in a historical table for record keeping"""
    history_data = resource.__dict__.copy()
    history_data.pop("_sa_instance_state")
    history_data.pop("id")
    history_data.pop("created_at")
    history_data.pop("updated_at")
    return history_data
