import { GpcStatus } from "fides-js";
import { Badge, Box, HStack, Stack, Text, WarningTwoIcon } from "fidesui";

import useI18n from "~/common/hooks/useI18n";

const BADGE_COLORS = {
  [GpcStatus.NONE]: undefined,
  [GpcStatus.APPLIED]: "green",
  [GpcStatus.OVERRIDDEN]: "red",
};

export const GpcBadge = ({ status }: { status: GpcStatus }) =>
  status === GpcStatus.NONE ? null : (
    <HStack data-testid="gpc-badge">
      <Text color="gray.600" fontWeight="semibold" fontSize="xs">
        Global Privacy Control
      </Text>
      <Badge variant="solid" colorScheme={BADGE_COLORS[status]}>
        {status}
      </Badge>
    </HStack>
  );

const InfoText: typeof Text = (props) => (
  <Box
    background="gray.100"
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
      background="gray.100"
      padding={4}
      spacing={1}
      lineHeight={5}
      data-testid="gpc-banner"
    >
      <Stack direction="row">
        <WarningTwoIcon color="blue.400" />
        <Text fontSize="sm" fontWeight="bold" data-testid="gpc.banner.title">
          {i18n.t("static.gpc.title")}
        </Text>
      </Stack>

      <Box paddingLeft={6} data-testid="gpc.banner.description">
        <Text fontSize="sm">{i18n.t("static.gpc.description")}</Text>
      </Box>
    </Stack>
  );
};
