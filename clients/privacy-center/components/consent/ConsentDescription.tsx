import { Box, Text, TextProps } from "@fidesui/react";
import { useAppSelector } from "~/app/hooks";
import { useConfig } from "~/features/common/config.slice";
import { selectIsNoticeDriven } from "~/features/common/settings.slice";
import { selectPrivacyExperience } from "~/features/consent/consent.slice";

const TEXT_PROPS: TextProps = {
  fontSize: ["small", "medium"],
  fontWeight: "medium",
  maxWidth: 624,
  textAlign: "center",
  color: "gray.600",
};

const ConsentDescription = () => {
  const config = useConfig();
  const isNoticeDriven = useAppSelector(selectIsNoticeDriven);
  const experience = useAppSelector(selectPrivacyExperience);

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
      {experience?.experience_config?.component_description}
    </Text>
  );
};

export default ConsentDescription;
