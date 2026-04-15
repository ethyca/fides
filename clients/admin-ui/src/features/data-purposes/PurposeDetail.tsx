import { Flex, Tag, Tabs, Text, Title, Tooltip } from "fidesui";

import PurposeConfigForm from "./PurposeConfigForm";
import PurposeDashboard from "./PurposeDashboard";
import type {
  DataPurpose,
  PurposeCoverage,
  PurposeDatasetAssignment,
  PurposeSystemAssignment,
} from "./types";

const MAX_VISIBLE_CATEGORIES = 5;

interface PurposeDetailProps {
  purpose: DataPurpose;
  coverage: PurposeCoverage;
  systems: PurposeSystemAssignment[];
  datasets: PurposeDatasetAssignment[];
}

interface LabeledTagsProps {
  label: string;
  values: string[];
  maxVisible?: number;
}

const LabeledTags = ({
  label,
  values,
  maxVisible,
}: LabeledTagsProps) => {
  if (values.length === 0) return null;
  const visible = maxVisible ? values.slice(0, maxVisible) : values;
  const remaining = maxVisible ? values.length - maxVisible : 0;
  const hiddenValues = remaining > 0 ? values.slice(maxVisible) : [];

  return (
    <Flex align="center" gap="small" wrap>
      <Text type="secondary" className="text-xs font-medium">
        {label}
      </Text>
      {visible.map((v) => (
        <Tag key={v} bordered={false}>
          {v}
        </Tag>
      ))}
      {remaining > 0 && (
        <Tooltip title={hiddenValues.join(", ")}>
          <Tag bordered={false} className="cursor-default">
            +{remaining} more
          </Tag>
        </Tooltip>
      )}
    </Flex>
  );
};

const PurposeDetail = ({
  purpose,
  coverage,
  systems,
  datasets,
}: PurposeDetailProps) => {
  const tabItems = [
    {
      key: "overview",
      label: "Overview",
      children: (
        <PurposeDashboard
          purpose={purpose}
          coverage={coverage}
          systems={systems}
          datasets={datasets}
        />
      ),
    },
    {
      key: "configuration",
      label: "Configuration",
      children: <PurposeConfigForm purpose={purpose} />,
    },
  ];

  return (
    <Flex vertical gap="middle" className="h-full overflow-y-auto pr-2">
      <div>
        <Title level={2} style={{ marginBottom: 8 }}>
          {purpose.name}
        </Title>
        <Text type="secondary">{purpose.description}</Text>
      </div>
      <Flex gap="middle" wrap align="center">
        <LabeledTags label="Data use" values={[purpose.data_use]} />
        <LabeledTags label="Subject" values={purpose.data_subjects} />
        <LabeledTags
          label="Data categories"
          values={purpose.data_categories}
          maxVisible={MAX_VISIBLE_CATEGORIES}
        />
      </Flex>
      <Tabs items={tabItems} defaultActiveKey="overview" />
    </Flex>
  );
};

export default PurposeDetail;
