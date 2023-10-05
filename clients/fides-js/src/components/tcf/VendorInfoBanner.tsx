import { h } from "preact";
import { useMemo } from "preact/hooks";
import { PrivacyExperience } from "../../lib/consent-types";
import { LegalBasisForProcessingEnum } from "../../lib/tcf/types";
import { vendorRecordsWithLegalBasis } from "../../lib/tcf/vendors";

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
      vendorRecordsWithLegalBasis(systems, LegalBasisForProcessingEnum.CONSENT)
        .length +
      vendorRecordsWithLegalBasis(vendors, LegalBasisForProcessingEnum.CONSENT)
        .length;

    // legint count
    const legint =
      vendorRecordsWithLegalBasis(
        systems,
        LegalBasisForProcessingEnum.LEGITIMATE_INTERESTS
      ).length +
      vendorRecordsWithLegalBasis(
        vendors,
        LegalBasisForProcessingEnum.LEGITIMATE_INTERESTS
      ).length;

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
