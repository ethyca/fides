import { Heading } from "fidesui";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import useI18n from "~/common/hooks/useI18n";
import { useConfig } from "~/features/common/config.slice";
import { selectIsNoticeDriven } from "~/features/common/settings.slice";

const ConsentHeading = () => {
  const config = useConfig();
  const isNoticeDriven = useAppSelector(selectIsNoticeDriven);
  const { i18n } = useI18n();

  const headingText = useMemo(() => {
    if (!isNoticeDriven) {
      return config.consent?.page.title;
    }

    return i18n.t("exp.title");
  }, [config, isNoticeDriven, i18n]);

  return (
    <Heading
      fontSize={["3xl", "4xl"]}
      color="gray.600"
      fontWeight="medium"
      textAlign="center"
      data-testid="consent-heading"
      mb={3}
    >
      {headingText}
    </Heading>
  );
};

export default ConsentHeading;
