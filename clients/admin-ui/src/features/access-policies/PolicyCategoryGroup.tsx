import { Col, Divider, Flex, Row, Tag, Text, Typography } from "fidesui";

import PolicyCard from "./PolicyCard";
import { PolicyCategory } from "./types";

const { Title } = Typography;

interface PolicyCategoryGroupProps {
  category: PolicyCategory;
  industryLabel?: string;
  onTogglePolicy: (id: string) => void;
}

const PolicyCategoryGroup = ({
  category,
  industryLabel,
  onTogglePolicy,
}: PolicyCategoryGroupProps) => {
  return (
    <div className="mb-8">
      <Flex align="center" gap="small">
        <Title level={5} className="!m-0">
          {category.title}
        </Title>
        {industryLabel && <Tag>{industryLabel} control</Tag>}
      </Flex>
      <Text type="secondary" size="sm" className="mt-1">
        Driven by: {category.drivenBy}
      </Text>
      <Divider className="mb-4 mt-2" />

      <Row gutter={[16, 16]}>
        {category.policies.map((policy) => (
          <Col key={policy.id} xs={24} md={8}>
            <PolicyCard policy={policy} onToggle={onTogglePolicy} />
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default PolicyCategoryGroup;
