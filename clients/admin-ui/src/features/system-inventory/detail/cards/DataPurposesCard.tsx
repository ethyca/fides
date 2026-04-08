import { Button, Card, Flex, Tag, Text } from "fidesui";

import type { MockPurpose } from "../../types";

interface DataPurposesCardProps {
  purposes: MockPurpose[];
}

const DataPurposesCard = ({ purposes }: DataPurposesCardProps) => (
  <Card
    title={
      <span className="text-[10px] uppercase tracking-wider">
        Data purposes
      </span>
    }
    size="small"
  >
    <Flex gap="small" wrap className="mb-2">
      {purposes.length > 0 ? (
        purposes.map((p) => (
          <Tag key={p.name} color={p.color as never} bordered={false}>
            {p.name}
          </Tag>
        ))
      ) : (
        <Text type="secondary">No purposes assigned</Text>
      )}
    </Flex>
    <Button type="link" size="small" className="!p-0">
      + Add
    </Button>
  </Card>
);

export default DataPurposesCard;
