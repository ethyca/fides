import { Box, Text, TextProps } from "fidesui";

import { useAppSelector } from "~/app/hooks";
import useI18n from "~/common/hooks/useI18n";
import { useConfig } from "~/features/common/config.slice";
import { selectIsNoticeDriven } from "~/features/common/settings.slice";

const TEXT_PROPS: TextProps = {
  fontSize: ["small", "medium"],
  fontWeight: "normal",
  maxWidth: 624,
  textAlign: "center",
  color: "gray.800",
};

const ConsentDescription = () => {
  const config = useConfig();
  const isNoticeDriven = useAppSelector(selectIsNoticeDriven);
  const { i18n } = useI18n();

  if (!isNoticeDriven) {
    return (
      <Box data-testid="consent-description">
        <Text {...TEXT_PROPS} data-testid="description">
          {config.consent?.page.description}
        </Text>
        {config.consent?.page.description_subtext?.map((paragraph, index) => (
          <Text
            {...TEXT_PROPS}
            // eslint-disable-next-line react/no-array-index-key
            key={`description-subtext${index}`}
          >
            {paragraph}
          </Text>
        ))}
      </Box>
    );
  }
  return (
    <Text {...TEXT_PROPS} data-testid="consent-description">
      {i18n.t("exp.description")}
    </Text>
  );
};

export default ConsentDescription;
