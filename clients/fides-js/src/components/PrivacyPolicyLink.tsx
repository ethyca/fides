import { h } from "preact";
import { ExperienceConfig } from "../lib/consent-types";
import type { I18n } from "../lib/i18n";

const PrivacyPolicyLink = ({
  experience,
  i18n
}: {
  experience?: ExperienceConfig;
  i18n: I18n;
}) => {

  // TODO: support checking if label doesn't exist
  const label = i18n.t("exp.privacy_policy_link_label");
  const url = i18n.t("exp.privacy_policy_url");
  if ( !label || !url ) {
    return null;
  }

  return (
    <div
      id="fides-privacy-policy-link"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <a
        href={url}
        rel="noopener noreferrer"
        target="_blank"
        className="fides-privacy-policy"
      >
        {label}
      </a>
    </div>
  );
};

export default PrivacyPolicyLink;
