import { Flex, Tabs, Tag, Text, Title, Tooltip } from "fidesui";

import AssignedDatasetsSection from "./AssignedDatasetsSection";
import AssignedSystemsSection from "./AssignedSystemsSection";
import type { DataPurpose } from "./data-purpose.slice";
import PurposeConfigForm from "./PurposeConfigForm";
import PurposeGovernanceAlert from "./PurposeGovernanceAlert";

const MAX_VISIBLE_CATEGORIES = 5;

interface PurposeDashboardProps {
  purpose: DataPurpose;
}

interface LabeledTagsProps {
  label: string;
  values: string[];
  maxVisible?: number;
}

const LabeledTags = ({ label, values, maxVisible }: LabeledTagsProps) => {
  if (values.length === 0) {
    return null;
  }
  const visible = maxVisible ? values.slice(0, maxVisible) : values;
  const remaining = maxVisible ? values.length - maxVisible : 0;
  const hiddenValues = remaining > 0 ? values.slice(maxVisible) : [];

  return (
    <Flex align="center" gap="small" wrap>
      <Text type="secondary" className="text-xs font-medium">
        {label}
      </Text>
      {visible.map((value) => (
        <Tag key={value} bordered={false}>
          {value}
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

const PurposeDashboard = ({ purpose }: PurposeDashboardProps) => {
  const tabItems = [
    {
      key: "overview",
      label: "Overview",
      children: (
        <Flex vertical gap="large">
          <PurposeGovernanceAlert fidesKey={purpose.fides_key} />
          <AssignedSystemsSection fidesKey={purpose.fides_key} />
          <AssignedDatasetsSection fidesKey={purpose.fides_key} />
        </Flex>
      ),
    },
    {
      key: "configuration",
      label: "Configuration",
      children: <PurposeConfigForm purpose={purpose} />,
    },
  ];

  return (
    <Flex vertical gap="middle">
      <div>
        <Title level={2} className="!mb-2">
          {purpose.name}
        </Title>
        <Text type="secondary">{purpose.description}</Text>
      </div>
      <Flex gap="middle" wrap align="center">
        <LabeledTags label="Data use" values={[purpose.data_use]} />
        {purpose.data_subject ? (
          <LabeledTags label="Subject" values={[purpose.data_subject]} />
        ) : null}
        <LabeledTags
          label="Data categories"
          values={purpose.data_categories ?? []}
          maxVisible={MAX_VISIBLE_CATEGORIES}
        />
      </Flex>
      <Tabs items={tabItems} defaultActiveKey="overview" />
    </Flex>
  );
};

export default PurposeDashboard;
