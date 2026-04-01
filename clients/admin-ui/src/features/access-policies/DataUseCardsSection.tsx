import { Col, Form, Row, Spin, Text } from "fidesui";

import DataUseCard from "./DataUseCard";
import type { DataUseOption } from "./types";

interface DataUseCardsSectionProps {
  industry: string | null;
  dataUses: DataUseOption[];
  isLoading: boolean;
  selectedDataUses: string[];
  onToggleDataUse: (id: string) => void;
}

const DataUseCardsSection = ({
  industry,
  dataUses,
  isLoading,
  selectedDataUses,
  onToggleDataUse,
}: DataUseCardsSectionProps) => {
  const renderContent = () => {
    if (!industry) {
      return (
        <div className="rounded-lg border border-dashed border-gray-300 px-6 py-10 text-center">
          <Text type="secondary">
            Select a business vertical above to see common data uses for your
            industry.
          </Text>
        </div>
      );
    }

    if (isLoading) {
      return (
        <div className="flex justify-center py-8">
          <Spin />
        </div>
      );
    }

    return (
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
    );
  };

  return (
    <div>
      <Form.Item label="Common data uses" className="!mb-2">
        <Text type="secondary" size="sm">
          Select the data use categories most relevant to your organization.
          This helps Fides prioritize scanning and generate more targeted access
          policies.
        </Text>
      </Form.Item>
      {renderContent()}
    </div>
  );
};

export default DataUseCardsSection;
