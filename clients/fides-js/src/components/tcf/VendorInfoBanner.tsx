import { h } from "preact";
import { useMemo } from "preact/hooks";
import { PrivacyExperience } from "../../lib/consent-types";
import {
  LegalBasisForProcessingEnum,
  TCFVendorRecord,
} from "../../lib/tcf/types";

const VendorInfo = ({
  label,
  count,
  onClick,
}: {
  label: string;
  count: number;
  onClick?: () => void;
}) => (
  <div className="fides-flex-center">
    {onClick ? (
      <button
        type="button"
        className="fides-link-button fides-vendor-info-label"
        onClick={onClick}
      >
        {label}
      </button>
    ) : (
      <span className="fides-vendor-info-label">{label}</span>
    )}{" "}
    <span className="fides-notice-badge">{count}</span>
  </div>
);

const countVendorRecordsWithLegalBasis = (
  records: TCFVendorRecord[],
  legalBasis: LegalBasisForProcessingEnum
) =>
  records.filter((record) => {
    const { purposes, special_purposes: specialPurposes } = record;
    const hasApplicablePurposes = purposes?.filter((purpose) =>
      purpose.legal_bases?.includes(legalBasis)
    );
    const hasApplicableSpecialPurposes = specialPurposes?.filter((purpose) =>
      purpose.legal_bases?.includes(legalBasis)
    );
    return (
      hasApplicablePurposes?.length || hasApplicableSpecialPurposes?.length
    );
  }).length;

const VendorInfoBanner = ({
  experience,
  goToVendorTab,
}: {
  experience: PrivacyExperience;
  goToVendorTab: () => void;
}) => {
  const counts = useMemo(() => {
    const { tcf_systems: systems = [], tcf_vendors: vendors = [] } = experience;
    // total count
    const total = systems.length + vendors.length;

    // consent count
    const consent =
      countVendorRecordsWithLegalBasis(
        systems,
        LegalBasisForProcessingEnum.CONSENT
      ) +
      countVendorRecordsWithLegalBasis(
        vendors,
        LegalBasisForProcessingEnum.CONSENT
      );

    // legint count
    const legint =
      countVendorRecordsWithLegalBasis(
        systems,
        LegalBasisForProcessingEnum.LEGITIMATE_INTERESTS
      ) +
      countVendorRecordsWithLegalBasis(
        vendors,
        LegalBasisForProcessingEnum.LEGITIMATE_INTERESTS
      );

    return { total, consent, legint };
  }, [experience]);

  return (
    <div className="fides-background-dark fides-vendor-info">
      <VendorInfo
        label="Vendors"
        count={counts.total}
        onClick={goToVendorTab}
      />
      <VendorInfo label="Vendors who use consent" count={counts.consent} />
      <VendorInfo
        label="Vendors who use legitimate interest"
        count={counts.legint}
      />
    </div>
  );
};

export default VendorInfoBanner;
