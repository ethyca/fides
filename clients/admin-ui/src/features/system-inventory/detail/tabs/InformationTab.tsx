import { Card, Descriptions, Tag, Text } from "fidesui";

import type { MockSystem } from "../../types";

interface InformationTabProps {
  system: MockSystem;
}

const InformationTab = ({ system }: InformationTabProps) => (
  <Card style={{ maxWidth: 800 }}>
    <Descriptions
      bordered
      column={2}
      size="small"
      title="System information"
    >
      <Descriptions.Item label="Name">
        <Text strong>{system.name}</Text>
      </Descriptions.Item>
      <Descriptions.Item label="Key">
        <Text copyable>{system.fides_key}</Text>
      </Descriptions.Item>
      <Descriptions.Item label="Type">
        {system.system_type}
      </Descriptions.Item>
      <Descriptions.Item label="Department">
        {system.department}
      </Descriptions.Item>
      <Descriptions.Item label="Responsibility">
        {system.responsibility}
      </Descriptions.Item>
      <Descriptions.Item label="Group">
        {system.group ?? "None"}
      </Descriptions.Item>
      <Descriptions.Item label="Description" span={2}>
        {system.description}
      </Descriptions.Item>
      <Descriptions.Item label="Stewards" span={2}>
        {system.stewards.length > 0
          ? system.stewards.map((st) => st.name).join(", ")
          : "None assigned"}
      </Descriptions.Item>
      <Descriptions.Item label="Roles" span={2}>
        {system.roles.map((r) => (
          <Tag key={r} bordered={false}>
            {r.charAt(0).toUpperCase() + r.slice(1)}
          </Tag>
        ))}
      </Descriptions.Item>
      <Descriptions.Item label="DSAR enabled">
        {system.privacyRequests.dsarEnabled ? (
          <Tag color="success" bordered={false}>Yes</Tag>
        ) : (
          <Tag color="error" bordered={false}>No</Tag>
        )}
      </Descriptions.Item>
    </Descriptions>
  </Card>
);

export default InformationTab;
