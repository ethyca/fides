import { Card, Divider, Flex, Tag, Text } from "fidesui";

import type { MockRelationship } from "../../types";

interface ProducerConsumerCardProps {
  relationships: MockRelationship[];
}

const RelationshipRow = ({ rel }: { rel: MockRelationship }) => (
  <Flex justify="space-between" align="center" className="py-2">
    <div>
      <Text strong>{rel.systemName}</Text>
      <br />
      <Text type="secondary" className="text-xs">
        Authorized uses: {rel.authorizedUses.join(", ")} &middot; Declared use:{" "}
        {rel.declaredUse}
      </Text>
      {rel.hasViolation ? (
        <div>
          <Text type="danger" className="text-xs">
            ● {rel.violationReason}
          </Text>
        </div>
      ) : (
        <div>
          <Text type="success" className="text-xs">
            Match — no violation
          </Text>
        </div>
      )}
    </div>
    <Tag bordered={false}>
      {rel.role === "producer" ? "Consumer" : "Producer"}
    </Tag>
  </Flex>
);

const ProducerConsumerCard = ({ relationships }: ProducerConsumerCardProps) => {
  const producingFor = relationships.filter((r) => r.role === "producer");
  const consumingFrom = relationships.filter((r) => r.role === "consumer");

  return (
    <Card
      title="Producer / consumer relationships"
      size="small"
      extra={
        <Text
          type="secondary"
          className="cursor-pointer text-xs hover:underline"
        >
          View data flow ›
        </Text>
      }
    >
      {producingFor.length > 0 && (
        <>
          <Text
            type="secondary"
            className="text-[10px] uppercase tracking-wider"
          >
            Producing for
          </Text>
          {producingFor.map((rel) => (
            <RelationshipRow key={rel.systemKey} rel={rel} />
          ))}
        </>
      )}
      {producingFor.length > 0 && consumingFrom.length > 0 && <Divider />}
      {consumingFrom.length > 0 && (
        <>
          <Text
            type="secondary"
            className="text-[10px] uppercase tracking-wider"
          >
            Consuming from
          </Text>
          {consumingFrom.map((rel) => (
            <RelationshipRow key={rel.systemKey} rel={rel} />
          ))}
        </>
      )}
      {relationships.length === 0 && (
        <Text type="secondary">No relationships configured</Text>
      )}
    </Card>
  );
};

export default ProducerConsumerCard;
