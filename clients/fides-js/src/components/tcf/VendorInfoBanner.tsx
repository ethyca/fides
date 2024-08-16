import { h } from "preact";
import { useEffect, useMemo } from "preact/hooks";

import { PrivacyExperience } from "../../lib/consent-types";
import type { I18n } from "../../lib/i18n";
import { useVendorButton } from "../../lib/tcf/vendor-button-context";

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
    <span className="fides-notice-badge">{count.toLocaleString()}</span>
  </div>
);

const VendorInfoBanner = ({
  experience,
  i18n,
  goToVendorTab,
}: {
  experience: PrivacyExperience;
  i18n: I18n;
  goToVendorTab: () => void;
}) => {
  const { setVendorCount } = useVendorButton();
  const counts = useMemo(() => {
    const {
      tcf_vendor_consents: consentVendors = [],
      tcf_vendor_legitimate_interests: legintVendors = [],
      tcf_system_consents: consentSystems = [],
      tcf_system_legitimate_interests: legintSystems = [],
      tcf_vendor_relationships: vendorRelationships = [],
      tcf_system_relationships: systemRelationships = [],
    } = experience;

    const total = vendorRelationships.length + systemRelationships.length;

    const consent = consentSystems.length + consentVendors.length;

    const legint = legintVendors.length + legintSystems.length;

    return { total, consent, legint };
  }, [experience]);

  useEffect(() => {
    if (counts.total && setVendorCount) {
      setVendorCount(counts.total);
    }
  }, [counts.total, setVendorCount]);

  return (
    <div className="fides-background-dark fides-vendor-info-banner">
      <VendorInfo
        label={i18n.t("static.tcf.vendors")}
        count={counts.total}
        onClick={goToVendorTab}
      />
      <VendorInfo
        label={i18n.t("static.tcf.vendors_using_consent")}
        count={counts.consent}
      />
      <VendorInfo
        label={i18n.t("static.tcf.vendors_using_legint")}
        count={counts.legint}
      />
    </div>
  );
};

export default VendorInfoBanner;
