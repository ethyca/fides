import { Card, Flex, Tag, Text } from "fidesui";

import { INTEGRATION_STATUS_COLORS } from "../../constants";
import type { MockSystem } from "../../types";

interface IntegrationsTabProps {
  system: MockSystem;
}

const IntegrationsTab = ({ system }: IntegrationsTabProps) => (
  <Flex vertical gap="middle" style={{ maxWidth: 800 }}>
    {system.integrations.length === 0 ? (
      <Text type="secondary">No integrations configured for this system.</Text>
    ) : (
      system.integrations.map((integ) => (
        <Card key={integ.name} size="small">
          <Flex justify="space-between" align="center">
            <div>
              <Text strong>{integ.name}</Text>
              <br />
              <Text type="secondary" className="text-xs">
                {integ.type} &middot; {integ.accessLevel} &middot; Last tested{" "}
                {integ.lastTested
                  ? new Date(integ.lastTested).toLocaleDateString()
                  : "never"}
              </Text>
              <br />
              <Text type="secondary" className="text-xs">
                Actions: {integ.enabledActions.join(", ")}
              </Text>
            </div>
            <Tag
              color={INTEGRATION_STATUS_COLORS[integ.status] as never}
              bordered={false}
            >
              {integ.status.charAt(0).toUpperCase() + integ.status.slice(1)}
            </Tag>
          </Flex>
        </Card>
      ))
    )}
  </Flex>
);

export default IntegrationsTab;
