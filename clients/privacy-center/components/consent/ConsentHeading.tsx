import { Heading } from "@fidesui/react";
import { useMemo } from "react";
import { useAppSelector } from "~/app/hooks";
import { useConfig } from "~/features/common/config.slice";
import { selectIsNoticeDriven } from "~/features/common/settings.slice";
import { selectPrivacyExperience } from "~/features/consent/consent.slice";

const ConsentHeading = () => {
  const config = useConfig();
  const isNoticeDriven = useAppSelector(selectIsNoticeDriven);
  const experience = useAppSelector(selectPrivacyExperience);

  const headingText = useMemo(() => {
    if (!isNoticeDriven) {
      return config.consent?.page.title;
    }

    return experience?.experience_config?.component_title;
  }, [config, isNoticeDriven, experience]);

  return (
    <Heading
      fontSize={["3xl", "4xl"]}
      color="gray.600"
      fontWeight="semibold"
      textAlign="center"
      data-testid="consent-heading"
    >
      {headingText}
    </Heading>
  );
};

export default ConsentHeading;
