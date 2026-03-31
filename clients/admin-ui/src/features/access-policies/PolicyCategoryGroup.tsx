import { Col, Divider, Flex, Row, Text, Typography } from "fidesui";

import { ControlGroup } from "./access-policies.slice";
import PolicyCard from "./PolicyCard";
import { AccessPolicyListItem } from "./types";

const { Title } = Typography;

interface PolicyCategoryGroupProps {
  controlGroup: ControlGroup;
  policies: AccessPolicyListItem[];
  onTogglePolicy: (policy: AccessPolicyListItem) => void;
  onEdit: (policy: AccessPolicyListItem) => void;
  onDuplicate: (policy: AccessPolicyListItem) => void;
  onDelete: (policy: AccessPolicyListItem) => void;
}

const PolicyCategoryGroup = ({
  controlGroup,
  policies,
  onTogglePolicy,
  onEdit,
  onDuplicate,
  onDelete,
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
        <Col key={policy.id} xs={24} md={8}>
          <PolicyCard
            policy={policy}
            onToggle={onTogglePolicy}
            onEdit={onEdit}
            onDuplicate={onDuplicate}
            onDelete={onDelete}
          />
        </Col>
      ))}
    </Row>
  </div>
);

export default PolicyCategoryGroup;
