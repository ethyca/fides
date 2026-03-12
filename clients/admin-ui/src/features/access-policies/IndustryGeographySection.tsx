import { Col, Form, Row, Select } from "fidesui";

import { GEOGRAPHY_OPTIONS, INDUSTRY_OPTIONS } from "./constants";

interface IndustryGeographySectionProps {
  industry: string | null;
  geography: string | null;
  onIndustryChange: (value: string) => void;
  onGeographyChange: (value: string) => void;
}

const IndustryGeographySection = ({
  industry,
  geography,
  onIndustryChange,
  onGeographyChange,
}: IndustryGeographySectionProps) => (
  <Row gutter={24}>
    <Col span={12}>
      <Form.Item
        label="Business vertical / industry"
        required
        htmlFor="industry-select"
        className="!mb-0"
      >
        <Select
          id="industry-select"
          aria-label="Business vertical / industry"
          className="w-full"
          placeholder="Select industry"
          value={industry}
          onChange={onIndustryChange}
          options={INDUSTRY_OPTIONS}
          allowClear
        />
      </Form.Item>
    </Col>
    <Col span={12}>
      <Form.Item label="Geography" htmlFor="geography-select" className="!mb-0">
        <Select
          id="geography-select"
          aria-label="Geography"
          className="w-full"
          placeholder="Select geography"
          value={geography}
          onChange={onGeographyChange}
          options={GEOGRAPHY_OPTIONS}
          allowClear
        />
      </Form.Item>
    </Col>
  </Row>
);

export default IndustryGeographySection;
