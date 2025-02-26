import { Link, LinkProps } from "fidesui";

import useI18n from "~/common/hooks/useI18n";
import { PrivacyExperienceResponse } from "~/types/api";

const PrivacyPolicyLink = ({
  experience,
  ...props
}: {
  experience?: PrivacyExperienceResponse;
} & Omit<LinkProps, "children">) => {
  const { selectExperienceConfigTranslation } = useI18n();
  if (!experience || !experience.experience_config) {
    return null;
  }

  const experienceConfigTranslation = selectExperienceConfigTranslation(
    experience.experience_config,
  );
  const { privacy_policy_link_label: label, privacy_policy_url: url } =
    experienceConfigTranslation;

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
      data-testid="privacypolicy.link"
      {...props}
    >
      {label}
    </Link>
  );
};

export default PrivacyPolicyLink;
