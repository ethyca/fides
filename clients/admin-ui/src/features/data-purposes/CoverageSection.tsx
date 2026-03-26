import { Flex, Progress, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

import type { DataPurpose, PurposeCoverage } from "./types";

interface CoverageSectionProps {
  purpose: DataPurpose;
  coverage: PurposeCoverage;
  systemCount?: number;
  datasetCount?: number;
}

const getCompleteness = (p: DataPurpose): number => {
  const checks = [
    !!p.description,
    !!p.data_use,
    p.data_categories.length > 0,
    p.data_subjects.length > 0,
    !!p.legal_basis,
    p.retention_period_days !== null,
    p.special_category_legal_basis !== null,
    p.features.length > 0,
  ];
  return Math.round((checks.filter(Boolean).length / checks.length) * 100);
};

const getStrokeColor = (percent: number) => {
  if (percent >= 80) return palette.FIDESUI_SUCCESS;
  if (percent >= 50) return palette.FIDESUI_WARNING;
  return palette.FIDESUI_ERROR;
};

const BORDER_COLOR = "#e8e8e8";

const Divider = () => (
  <div style={{ width: 1, height: 32, backgroundColor: BORDER_COLOR }} />
);

interface StatProps {
  value: number;
  label: string;
}

const Stat = ({ value, label }: StatProps) => (
  <Flex align="baseline" gap={6}>
    <Text strong className="text-base">
      {value}
    </Text>
    <Text type="secondary" className="text-sm">
      {label}
    </Text>
  </Flex>
);

const CoverageSection = ({ purpose, coverage, systemCount, datasetCount }: CoverageSectionProps) => {
  const completeness = getCompleteness(purpose);

  return (
    <Flex
      align="center"
      gap="large"
      style={{
        border: `1px solid ${BORDER_COLOR}`,
        borderRadius: 8,
        padding: "12px 24px",
      }}
    >
      <Flex align="center" gap={10}>
        <Progress
          type="circle"
          size={40}
          percent={completeness}
          strokeColor={getStrokeColor(completeness)}
          format={(p) => `${p}`}
        />
        <Text type="secondary" className="text-sm">
          Complete
        </Text>
      </Flex>
      <Divider />
      <Stat value={systemCount ?? coverage.systems.assigned} label="data consumers" />
      <Divider />
      <Stat value={datasetCount ?? coverage.datasets.assigned} label="datasets" />
      <Divider />
      <Stat value={coverage.tables.assigned} label="tables" />
    </Flex>
  );
};

export default CoverageSection;
