import { h } from "preact";
import { I18n, messageExists } from "../lib/i18n";

const PrivacyPolicyLink = ({ i18n }: { i18n: I18n }) => {
  // Privacy policy link is optional, so check if localized messages exist for
  // both the label & URL before attempting to render
  if (
    !messageExists(i18n, "exp.privacy_policy_link_label") ||
    !messageExists(i18n, "exp.privacy_policy_link_label")
  ) {
    return null;
  }
  const label = i18n.t("exp.privacy_policy_link_label");
  const url = i18n.t("exp.privacy_policy_url");

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
