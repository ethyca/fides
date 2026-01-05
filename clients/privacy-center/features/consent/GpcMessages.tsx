import { GpcStatus } from "fides-js";
import {
  ChakraBox as Box,
  ChakraHStack as HStack,
  ChakraStack as Stack,
  ChakraText as Text,
  ChakraWarningTwoIcon as WarningTwoIcon,
  CUSTOM_TAG_COLOR,
  Tag,
} from "fidesui";

import useI18n from "~/common/hooks/useI18n";

const BADGE_COLORS = {
  [GpcStatus.NONE]: undefined,
  [GpcStatus.APPLIED]: CUSTOM_TAG_COLOR.SUCCESS,
  [GpcStatus.OVERRIDDEN]: CUSTOM_TAG_COLOR.ERROR,
};

export const GpcBadge = ({ status }: { status: GpcStatus }) => {
  const { i18n } = useI18n();
  if (status === GpcStatus.NONE) {
    return null;
  }
  const statusLabel =
    status === GpcStatus.APPLIED
      ? i18n.t("exp.gpc_status_applied_label")
      : i18n.t("exp.gpc_status_overridden_label");
  return (
    <HStack data-testid="gpc-badge">
      <Text color="gray.800" fontWeight="semibold" fontSize="xs">
        {i18n.t("exp.gpc_label")}
      </Text>
      <Tag color={BADGE_COLORS[status]}>{statusLabel}</Tag>
    </HStack>
  );
};

const InfoText: typeof Text = (props) => (
  <Box
    background="gray.75"
    border="1px solid"
    borderColor="blue.50"
    borderRadius="md"
    fontSize="xs"
    paddingX={2}
    paddingY={3}
    mb={2}
  >
    <Text {...props} />
  </Box>
);

const GpcApplied = () => (
  <InfoText>
    You were opted out of this use case because of Global Privacy Controls.
  </InfoText>
);

const GpcOverridden = () => (
  <InfoText>
    The default Global Privacy Control for this use case has been overridden.
  </InfoText>
);

export const GpcInfo = ({ status }: { status: GpcStatus }) => {
  if (status === GpcStatus.APPLIED) {
    return <GpcApplied />;
  }

  if (status === GpcStatus.OVERRIDDEN) {
    return <GpcOverridden />;
  }

  return null;
};

export const GpcBanner = () => {
  const { i18n } = useI18n();

  return (
    <Stack
      border="1px solid"
      borderColor="blue.400"
      borderRadius="lg"
      background="gray.75"
      padding={4}
      spacing={1}
      lineHeight={5}
      data-testid="gpc-banner"
    >
      <Stack direction="row">
        <WarningTwoIcon color="blue.400" />
        <Text fontSize="sm" fontWeight="bold" data-testid="gpc.banner.title">
          {i18n.t("exp.gpc_title")}
        </Text>
      </Stack>

      <Box paddingLeft={6} data-testid="gpc.banner.description">
        <Text fontSize="sm">{i18n.t("exp.gpc_description")}</Text>
      </Box>
    </Stack>
  );
};
