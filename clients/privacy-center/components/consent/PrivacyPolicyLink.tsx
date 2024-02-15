import { Link, LinkProps } from "@fidesui/react";
import { PrivacyExperienceResponse } from "~/types/api";

const PrivacyPolicyLink = ({
  experience,
  ...props
}: {
  experience?: PrivacyExperienceResponse;
} & Omit<LinkProps, "children">) => {
  if (!experience || !experience.experience_config) {
    return null;
  }
  const { privacy_policy_link_label: label, privacy_policy_url: url } =
    experience.experience_config?.translations[0];

  if (!label || !url) {
    return null;
  }
  return (
    <Link
      href={url}
      textDecoration="underline"
      fontSize="sm"
      fontWeight="500"
      isExternal
      {...props}
    >
      {label}
    </Link>
  );
};

export default PrivacyPolicyLink;
