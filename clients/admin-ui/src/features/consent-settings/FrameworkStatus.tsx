import { Flex, Tag } from "fidesui";

import DocsLink from "~/features/common/DocsLink";

const FrameworkStatus = ({
  name,
  enabled,
}: {
  name: string;
  enabled: boolean;
}) => (
  <Flex vertical gap="small" className="text-sm font-medium">
    <span>
      {name} status{" "}
      {enabled ? (
        <Tag color="success">Enabled</Tag>
      ) : (
        <Tag color="error">Disabled</Tag>
      )}
    </span>
    <span>
      To {enabled ? "disable" : "enable"} {name}, please contact your Fides
      administrator or{" "}
      <DocsLink href="mailto:support@ethyca.com">Ethyca support</DocsLink>.
    </span>
  </Flex>
);

export default FrameworkStatus;
