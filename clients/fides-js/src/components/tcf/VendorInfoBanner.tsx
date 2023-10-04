import { h } from "preact";
import { useMemo } from "preact/hooks";
import { PrivacyExperience } from "../../lib/consent-types";

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
    const {
      tcf_consent_vendors: consentVendors = [],
      tcf_legitimate_interests_vendors: legintVendors = [],
      tcf_consent_systems: consentSystems = [],
      tcf_legitimate_interests_systems: legintSystems = [],
    } = experience;

    const total =
      consentSystems.length +
      consentVendors.length +
      legintVendors.length +
      legintSystems.length;

    const consent = consentSystems.length + consentVendors.length;

    const legint = legintVendors.length + legintSystems.length;

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
