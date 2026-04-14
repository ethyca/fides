import { Avatar, Button, Card, Flex, Space, Tag, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useState } from "react";

import AddIntegrationModal from "~/features/integrations/add-integration/AddIntegrationModal";

import { INTEGRATION_STATUS_COLORS } from "../../constants";
import type { MockIntegration } from "../../types";
import LinkExistingIntegrationModal from "../modals/LinkExistingIntegrationModal";

interface IntegrationsSummaryCardProps {
  integrations: MockIntegration[];
  systemFidesKey: string;
}

const IntegrationsSummaryCard = ({
  integrations,
  systemFidesKey,
}: IntegrationsSummaryCardProps) => {
  const [createOpen, setCreateOpen] = useState(false);
  const [linkOpen, setLinkOpen] = useState(false);

  return (
    <Card
      title="Integrations"
      size="small"
      extra={
        <Space size={4}>
          <Button type="link" size="small" onClick={() => setLinkOpen(true)}>
            Link existing
          </Button>
          <Button type="link" size="small" onClick={() => setCreateOpen(true)}>
            + Create
          </Button>
        </Space>
      }
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
              <Avatar
                size="small"
                style={{
                  backgroundColor: palette.FIDESUI_NEUTRAL_100,
                  color: palette.FIDESUI_NEUTRAL_800,
                  fontSize: 10,
                }}
              >
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
      <AddIntegrationModal
        isOpen={createOpen}
        onClose={() => setCreateOpen(false)}
      />
      <LinkExistingIntegrationModal
        open={linkOpen}
        onClose={() => setLinkOpen(false)}
        systemFidesKey={systemFidesKey}
      />
    </Card>
  );
};

export default IntegrationsSummaryCard;
