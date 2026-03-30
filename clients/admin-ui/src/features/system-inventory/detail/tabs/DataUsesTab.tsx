import { Card, Flex, Tag, Text } from "fidesui";

import type { MockSystem } from "../../types";

interface DataUsesTabProps {
  system: MockSystem;
}

const DataUsesTab = ({ system }: DataUsesTabProps) => (
  <Flex vertical gap="middle" style={{ maxWidth: 800 }}>
    {system.purposes.length === 0 ? (
      <Text type="secondary">No data uses declared for this system.</Text>
    ) : (
      system.purposes.map((p) => (
        <Card key={p.name} size="small">
          <Flex justify="space-between" align="center">
            <div>
              <Text strong>{p.name}</Text>
              <br />
              <Text type="secondary" className="text-xs">
                Data use purpose assigned to this system
              </Text>
            </div>
            <Tag color={p.color as never} bordered={false}>
              {p.name}
            </Tag>
          </Flex>
        </Card>
      ))
    )}
  </Flex>
);

export default DataUsesTab;
