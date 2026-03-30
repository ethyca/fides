import { Card, Divider, Flex, Tag, Text, Title } from "fidesui";

import type { MockSystem } from "../../types";

interface DataFlowTabProps {
  system: MockSystem;
}

const DataFlowTab = ({ system }: DataFlowTabProps) => {
  const producingFor = system.relationships.filter((r) => r.role === "producer");
  const consumingFrom = system.relationships.filter((r) => r.role === "consumer");

  return (
    <Flex vertical gap="large" style={{ maxWidth: 800 }}>
      {system.relationships.length === 0 ? (
        <Text type="secondary">No data flows configured for this system.</Text>
      ) : (
        <>
          {producingFor.length > 0 && (
            <Card size="small">
              <Title level={5}>Producing data for</Title>
              {producingFor.map((rel, i) => (
                <div key={rel.systemKey}>
                  <Flex
                    justify="space-between"
                    align="center"
                    className="py-2"
                  >
                    <div>
                      <Flex align="center" gap="small">
                        <Text strong>{system.name}</Text>
                        <Text type="secondary">→</Text>
                        <Text strong>{rel.systemName}</Text>
                      </Flex>
                      <Text type="secondary" className="text-xs">
                        Declared: {rel.declaredUse} &middot; Authorized:{" "}
                        {rel.authorizedUses.join(", ")}
                      </Text>
                    </div>
                    {rel.hasViolation ? (
                      <Tag color="error" bordered={false}>
                        Violation
                      </Tag>
                    ) : (
                      <Tag color="success" bordered={false}>
                        Match
                      </Tag>
                    )}
                  </Flex>
                  {i < producingFor.length - 1 && <Divider className="!my-0" />}
                </div>
              ))}
            </Card>
          )}
          {consumingFrom.length > 0 && (
            <Card size="small">
              <Title level={5}>Consuming data from</Title>
              {consumingFrom.map((rel, i) => (
                <div key={rel.systemKey}>
                  <Flex
                    justify="space-between"
                    align="center"
                    className="py-2"
                  >
                    <div>
                      <Flex align="center" gap="small">
                        <Text strong>{rel.systemName}</Text>
                        <Text type="secondary">→</Text>
                        <Text strong>{system.name}</Text>
                      </Flex>
                      <Text type="secondary" className="text-xs">
                        Declared: {rel.declaredUse} &middot; Authorized:{" "}
                        {rel.authorizedUses.join(", ")}
                      </Text>
                    </div>
                    {rel.hasViolation ? (
                      <Tag color="error" bordered={false}>
                        Violation
                      </Tag>
                    ) : (
                      <Tag color="success" bordered={false}>
                        Match
                      </Tag>
                    )}
                  </Flex>
                  {i < consumingFrom.length - 1 && (
                    <Divider className="!my-0" />
                  )}
                </div>
              ))}
            </Card>
          )}
        </>
      )}
    </Flex>
  );
};

export default DataFlowTab;
