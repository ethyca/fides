import { Avatar, Card, Flex, Tag, Text } from "fidesui";

import { INTEGRATION_STATUS_COLORS } from "../../constants";
import type { MockIntegration } from "../../types";

interface IntegrationsSummaryCardProps {
  integrations: MockIntegration[];
}

const IntegrationsSummaryCard = ({
  integrations,
}: IntegrationsSummaryCardProps) => (
  <Card
    title="Integrations"
    size="small"
    extra={<Text type="secondary" className="cursor-pointer text-xs hover:underline">Manage ›</Text>}
  >
    {integrations.length === 0 ? (
      <Text type="secondary">No integrations linked</Text>
    ) : (
      integrations.map((integ) => (
        <Flex
          key={integ.name}
          justify="space-between"
          align="center"
          className="py-2"
        >
          <Flex gap="small" align="center">
            <Avatar size="small" style={{ backgroundColor: "#e6e6e8", color: "#53575c", fontSize: 10 }}>
              {integ.type.slice(0, 2).toUpperCase()}
            </Avatar>
            <div>
              <Text strong className="text-sm">
                {integ.name}
              </Text>
              <br />
              <Text type="secondary" className="text-xs">
                Last tested{" "}
                {integ.lastTested
                  ? new Date(integ.lastTested).toLocaleDateString()
                  : "never"}{" "}
                &middot; {integ.enabledActions.join(", ")}
              </Text>
            </div>
          </Flex>
          <Tag
            color={INTEGRATION_STATUS_COLORS[integ.status] as never}
            bordered={false}
          >
            {integ.status.charAt(0).toUpperCase() + integ.status.slice(1)}
          </Tag>
        </Flex>
      ))
    )}
  </Card>
);

export default IntegrationsSummaryCard;
