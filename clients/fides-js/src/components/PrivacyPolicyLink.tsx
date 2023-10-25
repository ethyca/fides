import { h } from "preact";
import { ExperienceConfig } from "../lib/consent-types";

const PrivacyPolicyLink = ({
  experience,
}: {
  experience?: ExperienceConfig;
}) => {
  if (
    !experience?.privacy_policy_link_label ||
    !experience?.privacy_policy_url
  ) {
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
        href={experience.privacy_policy_url}
        rel="noopener noreferrer"
        target="_blank"
        className="fides-privacy-policy"
      >
        {experience.privacy_policy_link_label}
      </a>
    </div>
  );
};

export default PrivacyPolicyLink;
