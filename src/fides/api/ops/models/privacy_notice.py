from __future__ import annotations

from collections import defaultdict
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

from fideslang.validation import FidesKey
from sqlalchemy import Boolean, Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Session, relationship
from sqlalchemy.util import hybridproperty

from fides.api.ctl.sql_models import System  # type: ignore[attr-defined]
from fides.api.ops.common_exceptions import ValidationError
from fides.lib.db.base_class import Base, FidesBase


class PrivacyNoticeRegion(Enum):
    """
    Enum is not formalized in the DB because it is subject to frequent change
    """

    us_ca = "us_ca"  # california
    us_co = "us_co"  # colorado
    us_va = "us_va"  # virginia
    us_ut = "us_ut"  # utah
    eu_be = "eu_be"  # belgium
    eu_bg = "eu_bg"  # bulgaria
    eu_cz = "eu_cz"  # czechia
    eu_dk = "eu_dk"  # denmark
    eu_de = "eu_de"  # germany
    eu_ee = "eu_ee"  # estonia
    eu_ie = "eu_ie"  # ireland
    eu_el = "eu_el"  # greece
    eu_es = "eu_es"  # spain
    eu_fr = "eu_fr"  # france
    eu_hr = "eu_hr"  # croatia
    eu_it = "eu_it"  # italy
    eu_cy = "eu_cy"  # cyprus
    eu_lv = "eu_lv"  # latvia
    eu_lt = "eu_lt"  # lithuania
    eu_lu = "eu_lu"  # luxembourg
    eu_hu = "eu_hu"  # hungary
    eu_mt = "eu_mt"  # malta
    eu_nl = "eu_nl"  # netherlands
    eu_at = "eu_at"  # austria
    eu_pl = "eu_pl"  # poland
    eu_pt = "eu_pt"  # portugal
    eu_ro = "eu_ro"  # romania
    eu_si = "eu_si"  # slovenia
    eu_sk = "eu_sk"  # slovakia
    eu_fi = "eu_fi"  # finland
    eu_se = "eu_se"  # sweden


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
    Base class to establish the common columns for `PrivacyNotice`s and `PrivacyNoticeHistory`s
    """

    name = Column(String, nullable=False)
    description = Column(String)  # User-facing description
    internal_description = Column(String)  # Visible to internal users only
    origin = Column(String)  # pointer back to an origin template ID
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
    version = Column(Float, nullable=False, default=1.0)
    disabled = Column(Boolean, nullable=False, default=False)
    has_gpc_flag = Column(Boolean, nullable=False, default=False)
    displayed_in_privacy_center = Column(Boolean, nullable=False, default=True)
    displayed_in_overlay = Column(Boolean, nullable=False, default=True)
    displayed_in_api = Column(Boolean, nullable=False, default=True)

    def applies_to_system(self, system: System) -> bool:
        """Privacy Notice applies to System if a data use matches or the Privacy Notice
        Data Use is a parent of a System Data Use
        """
        for system_data_use in System.get_data_uses([system], include_parents=True):
            for privacy_notice_data_use in self.data_uses or []:
                if system_data_use == privacy_notice_data_use:
                    return True
        return False


class PrivacyNotice(PrivacyNoticeBase, Base):
    """
    A notice set up by a system administrator that an end user (i.e., data subject)
    accepts or rejects to indicate their consent for particular data uses
    """

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
        history_data = {**data, "privacy_notice_id": created.id}
        PrivacyNoticeHistory.create(db, data=history_data, check_name=False)
        return created

    def update(self, db: Session, *, data: dict[str, Any]) -> PrivacyNotice:
        """
        Overrides the base update method to automatically bump the version of the
        PrivacyNotice record and also create a new PrivacyNoticeHistory entry
        """

        # run through potential updates now
        for key, value in data.items():
            setattr(self, key, value)

        # only if there's a modification do we write the history record
        if db.is_modified(self):
            # on any update to a privacy notice record, its version must be incremented
            # version gets incremented by a full integer, i.e. 1.0 -> 2.0 -> 3.0
            self.version = float(self.version) + 1.0  # type: ignore
            self.save(db)

            # history record data is identical to the new privacy notice record data
            # except the notice's 'id' must be moved to the FK column
            # and is no longer the history record 'id' column
            history_data = {
                "name": self.name,
                "description": self.description or None,
                "origin": self.origin or None,
                "regions": self.regions,
                "consent_mechanism": self.consent_mechanism,
                "data_uses": self.data_uses,
                "enforcement_level": self.enforcement_level,
                "version": self.version,
                "disabled": self.disabled,
                "has_gpc_flag": self.has_gpc_flag,
                "displayed_in_privacy_center": self.displayed_in_privacy_center,
                "displayed_in_overlay": self.displayed_in_overlay,
                "displayed_in_api": self.displayed_in_api,
                "privacy_notice_id": self.id,
            }
            PrivacyNoticeHistory.create(db, data=history_data, check_name=False)

        return self

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


def check_conflicting_data_uses(
    new_privacy_notices: Iterable[PrivacyNotice],
    existing_privacy_notices: Iterable[PrivacyNotice],
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
    """
    # first, we map the existing [region -> data use] associations based on the set of
    # existing notices.
    # this gives us a simple "lookup table" for region and data use conflicts in incoming notices
    uses_by_region: Dict[PrivacyNoticeRegion, List[Tuple[str, str]]] = defaultdict(list)
    for privacy_notice in existing_privacy_notices:
        if privacy_notice.disabled:
            continue
        for region in privacy_notice.regions:
            for data_use in privacy_notice.data_uses:
                uses_by_region[PrivacyNoticeRegion(region)].append(
                    (data_use, privacy_notice.name)
                )

    # now, validate the new (incoming) notices
    for privacy_notice in new_privacy_notices:
        if privacy_notice.disabled:
            # if the incoming notice is disabled, it skips validation
            continue
        # check each of the incoming notice's regions
        for region in privacy_notice.regions:
            region_uses = uses_by_region[PrivacyNoticeRegion(region)]
            # check each of the incoming notice's data uses
            for data_use in privacy_notice.data_uses:
                for existing_use, notice_name in region_uses:
                    # we need to check for hierachical overlaps in _both_ directions
                    # i.e. whether the incoming DataUse is a parent _or_ a child of
                    # an existing DataUse
                    if new_data_use_conflicts_with_existing_use(existing_use, data_use):
                        raise ValidationError(
                            message=f"Privacy Notice '{notice_name}' has already assigned data use '{existing_use}' to region '{region}'"
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

    privacy_notice_id = Column(
        String, ForeignKey(PrivacyNotice.id_field_path), nullable=False
    )

    def calculate_relevant_systems(self, db: Session) -> List[FidesKey]:
        """Method to cache the relevant systems at the time to store on PrivacyPreferenceHistory for record keeping

        Provided the notice's enforcement level is "system_wide" - a system is relevant if
        their data use is an exact match or a child of the notice's data use.
        """
        relevant_systems: List[FidesKey] = []
        if self.enforcement_level == EnforcementLevel.system_wide:
            for system in db.query(System):
                if self.applies_to_system(system):
                    relevant_systems.append(system.fides_key)
                    continue
        return relevant_systems
