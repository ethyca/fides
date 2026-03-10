import { ChakraStack as Stack, ChakraText as Text, Tag } from "fidesui";

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
        <Tag color="success">Enabled</Tag>
      ) : (
        <Tag color="error">Disabled</Tag>
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
