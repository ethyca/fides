import {
  ArrowDownRightIcon,
  ColumnsType,
  CUSTOM_TAG_COLOR,
  GreenCheckCircleIcon,
  Icons,
  Layout,
  SparkleIcon as FidesUISparkleIcon,
  Table,
  Tag,
  TrashCanSolidIcon as FidesUITrashCanSolidIcon,
  Typography,
} from "fidesui";
import type { NextPage } from "next";
import React from "react";

import { ManualSetupIcon } from "~/features/common/Icon";
import { CompassIcon } from "~/features/common/Icon/CompassIcon";
import { MonitorIcon } from "~/features/common/Icon/MonitorIcon";
import { TagIcon } from "~/features/common/Icon/svg/TagIcon";
import { TrashCanOutlineIcon } from "~/features/common/Icon/TrashCanOutlineIcon";
import { TrashCanSolidIcon as AdminTrashCanSolidIcon } from "~/features/common/Icon/TrashCanSolidIcon";
import PageHeader from "~/features/common/PageHeader";

const { Content } = Layout;
const { Text } = Typography;

type IconType = "createIcon" | "chakra-icon" | "custom-svg";

type IconEntry = {
  key: string;
  currentName: string;
  currentIcon: React.ReactNode;
  iconType: IconType;
  source: "fidesui" | "admin-ui";
  suggestedCarbon: string | null;
  notes: string;
};

/** Wrapper to render raw SVG icons at a consistent size */
const SvgIconBox = ({ children }: { children: React.ReactNode }) => (
  <span
    style={{
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      width: 20,
      height: 20,
    }}
  >
    {children}
  </span>
);

const ICON_DATA: IconEntry[] = [
  // fidesui icons
  {
    key: "fidesui-ArrowDownRightIcon",
    currentName: "ArrowDownRightIcon",
    currentIcon: <ArrowDownRightIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: null,
    notes: "Used as child/sub-item indicator in ConsentAutomationForm",
  },
  {
    key: "fidesui-GreenCheckCircleIcon",
    currentName: "GreenCheckCircleIcon",
    currentIcon: <GreenCheckCircleIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: "CheckmarkFilled",
    notes: "Uses green fill color",
  },
  {
    key: "fidesui-TrashCanSolidIcon",
    currentName: "TrashCanSolidIcon",
    currentIcon: <FidesUITrashCanSolidIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: "TrashCan",
    notes: "",
  },
  {
    key: "fidesui-SparkleIcon",
    currentName: "SparkleIcon",
    currentIcon: <FidesUISparkleIcon width={20} height={20} />,
    iconType: "custom-svg",
    source: "fidesui",
    suggestedCarbon: "MagicWandFilled",
    notes: "Plus-only, AI/magic indicator",
  },

  // admin-ui custom icons
  {
    key: "admin-CompassIcon",
    currentName: "CompassIcon",
    currentIcon: <CompassIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "",
  },
  {
    key: "admin-ManualSetupIcon",
    currentName: "ManualSetupIcon",
    currentIcon: <ManualSetupIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: "WebServicesDefinition",
    notes: "",
  },
  {
    key: "admin-MonitorIcon",
    currentName: "MonitorIcon",
    currentIcon: <MonitorIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: "Dashboard",
    notes: "",
  },
  {
    key: "admin-TrashCanOutlineIcon",
    currentName: "TrashCanOutlineIcon",
    currentIcon: <TrashCanOutlineIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: "TrashCan",
    notes: "Outline variant",
  },
  {
    key: "admin-TrashCanSolidIcon",
    currentName: "TrashCanSolidIcon",
    currentIcon: <AdminTrashCanSolidIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: "TrashCan",
    notes: "Duplicate of fidesui version",
  },
  {
    key: "admin-TagIcon",
    currentName: "TagIcon",
    currentIcon: (
      <SvgIconBox>
        <TagIcon width={20} height={20} />
      </SvgIconBox>
    ),
    iconType: "custom-svg",
    source: "admin-ui",
    suggestedCarbon: "Tag",
    notes: "svg/ subdirectory",
  },
];

const IconsRecord = Icons as Record<
  string,
  React.ComponentType<{ size?: number }>
>;

const renderCarbonIcon = (name: string | null) => {
  if (!name) {
    return <Text type="secondary">No equivalent</Text>;
  }
  const CarbonIcon = IconsRecord[name];
  if (!CarbonIcon) {
    return (
      <Text type="warning">
        {name} <Text type="secondary">(not found)</Text>
      </Text>
    );
  }
  return (
    <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <CarbonIcon size={20} />
      <Text code>{name}</Text>
    </span>
  );
};

const columns: ColumnsType<IconEntry> = [
  {
    title: "Current Icon",
    dataIndex: "currentIcon",
    width: 70,
    render: (icon: React.ReactNode) => (
      <span
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {icon}
      </span>
    ),
  },
  {
    title: "Current Name",
    dataIndex: "currentName",
    sorter: (a, b) => a.currentName.localeCompare(b.currentName),
    defaultSortOrder: "ascend",
  },
  {
    title: "Source",
    dataIndex: "source",
    filters: [
      { text: "fidesui", value: "fidesui" },
      { text: "admin-ui", value: "admin-ui" },
    ],
    onFilter: (value, record) => record.source === value,
    render: (source: string) => (
      <Tag color={source === "fidesui" ? "info" : "default"}>{source}</Tag>
    ),
  },
  {
    title: "Icon Type",
    dataIndex: "iconType",
    filters: [
      { text: "createIcon", value: "createIcon" },
      { text: "Chakra Icon", value: "chakra-icon" },
      { text: "Custom SVG", value: "custom-svg" },
    ],
    onFilter: (value, record) => record.iconType === value,
    render: (iconType: IconType) => {
      const labels: Record<
        IconType,
        { text: string; color: CUSTOM_TAG_COLOR }
      > = {
        createIcon: { text: "createIcon", color: CUSTOM_TAG_COLOR.CORINTH },
        "chakra-icon": { text: "Chakra Icon", color: CUSTOM_TAG_COLOR.OLIVE },
        "custom-svg": { text: "Custom SVG", color: CUSTOM_TAG_COLOR.SANDSTONE },
      };
      const { text, color } = labels[iconType];
      return <Tag color={color}>{text}</Tag>;
    },
  },
  {
    title: "Suggested Carbon Equivalent",
    dataIndex: "suggestedCarbon",
    render: renderCarbonIcon,
  },
  {
    title: "Notes",
    dataIndex: "notes",
    render: (notes: string) =>
      notes ? <Text type="secondary">{notes}</Text> : null,
  },
];

const IconMigrationPage: NextPage = () => {
  return (
    <Layout>
      <Content className="overflow-auto px-10 py-6">
        <PageHeader heading="Icon Migration Reference" />
        <Text type="secondary" className="mb-4 block">
          Reference table for ENG-3081. Lists all non-Carbon icons still in use
          with suggested Carbon replacements for designer review.
        </Text>
        <Table<IconEntry>
          columns={columns}
          dataSource={ICON_DATA}
          pagination={false}
          size="middle"
        />
      </Content>
    </Layout>
  );
};

export default IconMigrationPage;
