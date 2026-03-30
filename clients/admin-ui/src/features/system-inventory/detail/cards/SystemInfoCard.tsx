import { Card, Descriptions, Tag, Text } from "fidesui";

import type { MockSystem } from "../../types";

interface SystemInfoCardProps {
  system: MockSystem;
}

const SystemInfoCard = ({ system }: SystemInfoCardProps) => (
  <Card title={<span className="text-[10px] uppercase tracking-wider">System info</span>} size="small">
    <Descriptions column={1} size="small">
      <Descriptions.Item label="Type">
        <Text strong>{system.system_type}</Text>
      </Descriptions.Item>
      <Descriptions.Item label="Department">
        <Text strong>{system.department}</Text>
      </Descriptions.Item>
      <Descriptions.Item label="Responsibility">
        <Text strong>{system.responsibility}</Text>
      </Descriptions.Item>
      <Descriptions.Item label="DSAR">
        {system.privacyRequests.dsarEnabled ? (
          <Tag color="success" bordered={false}>
            Ready
          </Tag>
        ) : (
          <Tag color="error" bordered={false}>
            Not ready
          </Tag>
        )}
      </Descriptions.Item>
      {system.group && (
        <Descriptions.Item label="Group">
          <Text strong>{system.group}</Text>
        </Descriptions.Item>
      )}
    </Descriptions>
  </Card>
);

export default SystemInfoCard;
