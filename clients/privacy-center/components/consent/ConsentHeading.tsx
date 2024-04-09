import { Heading } from "@fidesui/react";
import { useMemo } from "react";
import { useAppSelector } from "~/app/hooks";
import { useI18n } from "~/common/i18nContext";
import { useConfig } from "~/features/common/config.slice";
import { selectIsNoticeDriven } from "~/features/common/settings.slice";
import { selectPrivacyExperience } from "~/features/consent/consent.slice";

const ConsentHeading = () => {
  const config = useConfig();
  const isNoticeDriven = useAppSelector(selectIsNoticeDriven);
  const experience = useAppSelector(selectPrivacyExperience);
  const { i18n } = useI18n();

  const headingText = useMemo(() => {
    if (!isNoticeDriven) {
      return config.consent?.page.title;
    }

    return i18n.t("exp.title");
  }, [config, isNoticeDriven, experience, i18n]);

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
