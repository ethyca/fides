import { Col, Form, Row, Text } from "fidesui";

import { DATA_USES_BY_INDUSTRY, DEFAULT_DATA_USES } from "./constants";
import DataUseCard from "./DataUseCard";

interface DataUseCardsSectionProps {
  industry: string | null;
  selectedDataUses: string[];
  onToggleDataUse: (id: string) => void;
}

const DataUseCardsSection = ({
  industry,
  selectedDataUses,
  onToggleDataUse,
}: DataUseCardsSectionProps) => {
  const dataUses = industry
    ? (DATA_USES_BY_INDUSTRY[industry] ?? DEFAULT_DATA_USES)
    : DEFAULT_DATA_USES;

  const industryLabel = industry
    ? industry.charAt(0).toUpperCase() + industry.slice(1)
    : "General";

  return (
    <div>
      <Form.Item
        label={`Common data uses (${industryLabel})`}
        className="!mb-2"
      >
        <Text type="secondary" size="sm">
          Select the data use categories most relevant to your organization.
          This helps Fides prioritize scanning and generate more targeted access
          policies.
        </Text>
      </Form.Item>
      <Row gutter={[12, 12]}>
        {dataUses.map((dataUse) => (
          <Col key={dataUse.id} xs={24} md={12}>
            <DataUseCard
              title={dataUse.title}
              iconName={dataUse.iconName}
              isSelected={selectedDataUses.includes(dataUse.id)}
              onClick={() => onToggleDataUse(dataUse.id)}
            />
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default DataUseCardsSection;
