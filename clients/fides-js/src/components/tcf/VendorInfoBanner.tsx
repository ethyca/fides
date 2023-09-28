import { h } from "preact";
import { useMemo } from "preact/hooks";
import { PrivacyExperience } from "../../lib/consent-types";
import {
  LegalBasisForProcessingEnum,
  TCFVendorRecord,
} from "../../lib/tcf/types";

const VendorInfo = ({ label, count }: { label: string; count: number }) => (
  <div className="fides-flex-center">
    <span className="fides-vendor-info-label">{label}</span>{" "}
    <span className="fides-notice-badge">{count}</span>
  </div>
);

const countVendorRecordsWithLegalBasis = (
  records: TCFVendorRecord[],
  legalBasis: LegalBasisForProcessingEnum
) =>
  records.filter((record) => {
    const { purposes, special_purposes: specialPurposes } = record;
    const hasConsentPurposes = purposes?.filter((purpose) =>
      purpose.legal_bases?.includes(legalBasis)
    );
    const hasConsentSpecialPurposes = specialPurposes?.filter((purpose) =>
      purpose.legal_bases?.includes(legalBasis)
    );
    return hasConsentPurposes || hasConsentSpecialPurposes;
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
      <VendorInfo label="Vendors" count={counts.total} />
      <VendorInfo label="Vendors who use consent" count={counts.consent} />
      <VendorInfo
        label="Vendors who use legitimate interest"
        count={counts.legint}
      />
      <button
        type="button"
        className="fides-link-button"
        onClick={goToVendorTab}
      >
        View our partner{counts.total === 1 ? "" : "s"}
      </button>
    </div>
  );
};

export default VendorInfoBanner;
