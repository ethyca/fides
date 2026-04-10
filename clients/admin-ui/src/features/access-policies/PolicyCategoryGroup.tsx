import { Col, Divider, Flex, Row, Text, Typography } from "fidesui";

import { Control } from "./access-policies.slice";
import PolicyCard from "./PolicyCard";
import { AccessPolicyListItem } from "./types";

const { Title } = Typography;

interface PolicyCategoryGroupProps {
  controlGroup: Control;
  policies: AccessPolicyListItem[];
  onTogglePolicy: (policy: AccessPolicyListItem) => void;
}

const PolicyCategoryGroup = ({
  controlGroup,
  policies,
  onTogglePolicy,
}: PolicyCategoryGroupProps) => (
  <div className="mb-8">
    <Flex align="center" gap="small">
      <Title level={5} className="!m-0">
        {controlGroup.label}
      </Title>
    </Flex>
    <Text type="secondary" size="sm" className="mt-1">
      {policies.length} {policies.length === 1 ? "policy" : "policies"}
    </Text>
    <Divider className="mb-4 mt-2" />

    <Row gutter={[16, 16]}>
      {policies.map((policy) => (
        <Col key={policy.id} md={8} xxl={6}>
          <PolicyCard policy={policy} onToggle={onTogglePolicy} />
        </Col>
      ))}
    </Row>
  </div>
);

export default PolicyCategoryGroup;
