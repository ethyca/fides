import { Button, Card, Flex, Tag, Text } from "fidesui";
import { useState } from "react";

import AddIntegrationModal from "~/features/integrations/add-integration/AddIntegrationModal";

import { INTEGRATION_STATUS_COLORS } from "../../constants";
import type { MockSystem } from "../../types";
import LinkExistingIntegrationModal from "../modals/LinkExistingIntegrationModal";

interface IntegrationsTabProps {
  system: MockSystem;
}

const IntegrationsTab = ({ system }: IntegrationsTabProps) => {
  const [createOpen, setCreateOpen] = useState(false);
  const [linkOpen, setLinkOpen] = useState(false);

  return (
    <Flex vertical gap="middle" style={{ maxWidth: 800 }}>
      <Flex justify="flex-end" gap="small">
        <Button onClick={() => setLinkOpen(true)}>Link existing</Button>
        <Button type="primary" onClick={() => setCreateOpen(true)}>
          + Create integration
        </Button>
      </Flex>
      {system.integrations.length === 0 ? (
        <Text type="secondary">
          No integrations configured for this system.
        </Text>
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
      <AddIntegrationModal
        isOpen={createOpen}
        onClose={() => setCreateOpen(false)}
      />
      <LinkExistingIntegrationModal
        open={linkOpen}
        onClose={() => setLinkOpen(false)}
        systemFidesKey={system.fides_key}
      />
    </Flex>
  );
};

export default IntegrationsTab;
