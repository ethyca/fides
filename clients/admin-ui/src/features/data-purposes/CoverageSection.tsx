import { Flex, Progress, Text } from "fidesui";

import { getCompleteness, getStrokeColor } from "./purposeUtils";
import type { DataPurpose, PurposeCoverage } from "./types";

interface CoverageSectionProps {
  purpose: DataPurpose;
  coverage: PurposeCoverage;
  systemCount?: number;
  datasetCount?: number;
}

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
