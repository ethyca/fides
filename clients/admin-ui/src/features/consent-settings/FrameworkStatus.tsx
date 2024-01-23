import { Badge, Stack, Text } from "@fidesui/react";

import DocsLink from "~/features/common/DocsLink";

const FrameworkStatus = ({
  name,
  enabled,
}: {
  name: string;
  enabled: boolean;
}) => (
  <Stack
    spacing={2}
    fontSize="sm"
    lineHeight="5"
    fontWeight="medium"
    color="gray.700"
  >
    <Text>
      {name} status{" "}
      {enabled ? (
        <Badge
          fontWeight="semibold"
          color="green.800"
          backgroundColor="green.100"
        >
          Enabled
        </Badge>
      ) : (
        <Badge fontWeight="semibold" backgroundColor="red.100">
          Disabled
        </Badge>
      )}
    </Text>
    <Text>
      To {enabled ? "disable" : "enable"} {name}, please contact your Fides
      administrator or{" "}
      <DocsLink href="mailto:support@ethyca.com">Ethyca support</DocsLink>.
    </Text>
  </Stack>
);

export default FrameworkStatus;
