import { Card, Descriptions, Text } from "fidesui";

import type { MockPrivacyRequests } from "../../types";

interface PrivacyRequestsCardProps {
  requests: MockPrivacyRequests;
}

const PrivacyRequestsCard = ({ requests }: PrivacyRequestsCardProps) => (
  <Card
    title={
      <span className="text-[10px] uppercase tracking-wider">
        Privacy requests
      </span>
    }
    size="small"
  >
    <Descriptions column={1} size="small">
      <Descriptions.Item label="Open">
        <Text strong>{requests.open}</Text>
      </Descriptions.Item>
      <Descriptions.Item label="Closed">
        <Text strong>{requests.closed}</Text>
      </Descriptions.Item>
      <Descriptions.Item label="Avg access">
        <Text strong>{requests.avgAccessDays}d</Text>
      </Descriptions.Item>
      <Descriptions.Item label="Avg erasure">
        <Text strong>{requests.avgErasureDays}d</Text>
      </Descriptions.Item>
    </Descriptions>
  </Card>
);

export default PrivacyRequestsCard;
