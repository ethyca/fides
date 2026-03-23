import {
  AddIcon as FidesUIAddIcon,
  ArrowDownLineIcon,
  ArrowDownRightIcon,
  ArrowUpLineIcon,
  CloseSolidIcon,
  ColumnsType,
  DownloadSolidIcon,
  EyeIcon,
  FilterIcon,
  FilterLightIcon,
  GearIcon,
  GreenCheckCircleIcon,
  GreenCircleIcon,
  GripDotsVerticalIcon,
  Icons,
  Layout,
  LinkIcon as FidesUILinkIcon,
  MoreIcon,
  SearchLineIcon,
  SortArrowIcon,
  SparkleIcon as FidesUISparkleIcon,
  StepperCircleCheckmarkIcon,
  StepperCircleIcon,
  Table,
  Tag,
  TrashCanSolidIcon as FidesUITrashCanSolidIcon,
  Typography,
  UserIcon,
  VerticalLineIcon,
  YellowWarningIcon,
} from "fidesui";
import type { NextPage } from "next";
import React from "react";

import SlackIconChat from "~/features/chat-provider/icons/SlackIcon";
import { AddIcon as CustomFieldsAddIcon } from "~/features/common/custom-fields/icons/AddIcon";
import {
  AWSLogoIcon,
  CopyIcon,
  DisplayAllIcon,
  DownloadLightIcon,
  GearLightIcon,
  GlobeIcon,
  GroupedIcon,
  ManualSetupIcon,
  OktaLogoIcon,
} from "~/features/common/Icon";
import { CompassIcon } from "~/features/common/Icon/CompassIcon";
import { DatabaseIcon } from "~/features/common/Icon/database/DatabaseIcon";
import { DatasetIcon } from "~/features/common/Icon/database/DatasetIcon";
import { FieldIcon } from "~/features/common/Icon/database/FieldIcon";
import { TableIcon as DBTableIcon } from "~/features/common/Icon/database/TableIcon";
import { MonitorIcon } from "~/features/common/Icon/MonitorIcon";
import { MonitorOffIcon } from "~/features/common/Icon/MonitorOffIcon";
import { MonitorOnIcon } from "~/features/common/Icon/MonitorOnIcon";
import NextArrow from "~/features/common/Icon/NextArrow";
import { PlayIcon } from "~/features/common/Icon/Play";
import PrevArrow from "~/features/common/Icon/PrevArrow";
import RightArrow from "~/features/common/Icon/RightArrow";
import { SparkleIcon as AdminSparkleIcon } from "~/features/common/Icon/SparkleIcon";
import { RightDownArrowIcon } from "~/features/common/Icon/svg/RightDownArrowIcon";
import { RightUpArrowIcon } from "~/features/common/Icon/svg/RightUpArrowIcon";
import { TagIcon } from "~/features/common/Icon/svg/TagIcon";
import { TrashCanOutlineIcon } from "~/features/common/Icon/TrashCanOutlineIcon";
import { TrashCanSolidIcon as AdminTrashCanSolidIcon } from "~/features/common/Icon/TrashCanSolidIcon";
import PageHeader from "~/features/common/PageHeader";
import AwsIcon from "~/features/messaging/icons/AwsIcon";
import MailgunIcon from "~/features/messaging/icons/MailgunIcon";
import TwilioIcon from "~/features/messaging/icons/TwilioIcon";
import { SlackIcon as AssessmentsSlackIcon } from "~/features/privacy-assessments/SlackIcon";

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
    key: "fidesui-AddIcon",
    currentName: "AddIcon",
    currentIcon: <FidesUIAddIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: null,
    notes: "Unused, remove from fidesui",
  },
  {
    key: "fidesui-ArrowDownLineIcon",
    currentName: "ArrowDownLineIcon",
    currentIcon: <ArrowDownLineIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: "ChevronDown",
    notes: "",
  },
  {
    key: "fidesui-ArrowDownRightIcon",
    currentName: "ArrowDownRightIcon",
    currentIcon: <ArrowDownRightIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: "Corner",
    notes: "Used as child/sub-item indicator in ConsentAutomationForm",
  },
  {
    key: "fidesui-ArrowUpLineIcon",
    currentName: "ArrowUpLineIcon",
    currentIcon: <ArrowUpLineIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: null,
    notes: "Unused, remove from fidesui",
  },
  {
    key: "fidesui-CloseSolidIcon",
    currentName: "CloseSolidIcon",
    currentIcon: <CloseSolidIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: null,
    notes: "Unused, remove from fidesui",
  },
  {
    key: "fidesui-DownloadSolidIcon",
    currentName: "DownloadSolidIcon",
    currentIcon: <DownloadSolidIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: null,
    notes: "Unused, remove from fidesui",
  },
  {
    key: "fidesui-EyeIcon",
    currentName: "EyeIcon",
    currentIcon: <EyeIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: "View",
    notes: "",
  },
  {
    key: "fidesui-GearIcon",
    currentName: "GearIcon",
    currentIcon: <GearIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: null,
    notes: "Unused, remove from fidesui",
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
    key: "fidesui-LinkIcon",
    currentName: "LinkIcon",
    currentIcon: <FidesUILinkIcon boxSize={5} />,
    iconType: "chakra-icon",
    source: "fidesui",
    suggestedCarbon: "Link",
    notes: "",
  },
  {
    key: "fidesui-MoreIcon",
    currentName: "MoreIcon",
    currentIcon: <MoreIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: "OverflowMenuHorizontal",
    notes: "",
  },
  {
    key: "fidesui-SearchLineIcon",
    currentName: "SearchLineIcon",
    currentIcon: <SearchLineIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: "Search",
    notes: "",
  },
  {
    key: "fidesui-SortArrowIcon",
    currentName: "SortArrowIcon",
    currentIcon: <SortArrowIcon />,
    iconType: "chakra-icon",
    source: "fidesui",
    suggestedCarbon: null,
    notes: "Unused, remove from fidesui",
  },
  {
    key: "fidesui-StepperCircleIcon",
    currentName: "StepperCircleIcon",
    currentIcon: <StepperCircleIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: null,
    notes: "Unused, remove from fidesui",
  },
  {
    key: "fidesui-StepperCircleCheckmarkIcon",
    currentName: "StepperCircleCheckmarkIcon",
    currentIcon: <StepperCircleCheckmarkIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: null,
    notes: "Unused, remove from fidesui",
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
    key: "fidesui-UserIcon",
    currentName: "UserIcon",
    currentIcon: <UserIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: null,
    notes: "Unused, remove from fidesui",
  },
  {
    key: "fidesui-VerticalLineIcon",
    currentName: "VerticalLineIcon",
    currentIcon: <VerticalLineIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: null,
    notes: "Unused, remove from fidesui",
  },
  {
    key: "fidesui-YellowWarningIcon",
    currentName: "YellowWarningIcon",
    currentIcon: <YellowWarningIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: null,
    notes: "Unused, remove from fidesui",
  },
  {
    key: "fidesui-FilterIcon",
    currentName: "FilterIcon",
    currentIcon: <FilterIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: null,
    notes: "Unused, remove from fidesui",
  },
  {
    key: "fidesui-FilterLightIcon",
    currentName: "FilterLightIcon",
    currentIcon: <FilterLightIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: null,
    notes: "Unused, remove from fidesui",
  },
  {
    key: "fidesui-GreenCircleIcon",
    currentName: "GreenCircleIcon",
    currentIcon: <GreenCircleIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: null,
    notes: "Unused, remove from fidesui",
  },
  {
    key: "fidesui-GripDotsVerticalIcon",
    currentName: "GripDotsVerticalIcon",
    currentIcon: <GripDotsVerticalIcon boxSize={5} />,
    iconType: "createIcon",
    source: "fidesui",
    suggestedCarbon: "Draggable",
    notes: "Plus-only",
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
    key: "admin-AWSLogoIcon",
    currentName: "AWSLogoIcon",
    currentIcon: <AWSLogoIcon />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "Brand logo, no Carbon equivalent",
  },
  {
    key: "admin-CompassIcon",
    currentName: "CompassIcon",
    currentIcon: <CompassIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: "Compass",
    notes: "",
  },
  {
    key: "admin-CopyIcon",
    currentName: "CopyIcon",
    currentIcon: <CopyIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: "Copy",
    notes: "",
  },
  {
    key: "admin-DisplayAllIcon",
    currentName: "DisplayAllIcon",
    currentIcon: <DisplayAllIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: "ExpandAll",
    notes: "Used as 'Expand all' toggle in table column headers",
  },
  {
    key: "admin-DownloadLightIcon",
    currentName: "DownloadLightIcon",
    currentIcon: <DownloadLightIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: "Download",
    notes: "Light variant",
  },
  {
    key: "admin-GearLightIcon",
    currentName: "GearLightIcon",
    currentIcon: <GearLightIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: "Settings",
    notes: "Light variant",
  },
  {
    key: "admin-GlobeIcon",
    currentName: "GlobeIcon",
    currentIcon: <GlobeIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "Unused, remove from admin-ui",
  },
  {
    key: "admin-GroupedIcon",
    currentName: "GroupedIcon",
    currentIcon: <GroupedIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: "CollapseAll",
    notes: "Used as 'Collapse all' toggle in table column headers",
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
    key: "admin-MonitorOffIcon",
    currentName: "MonitorOffIcon",
    currentIcon: <MonitorOffIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "Unused, remove from admin-ui",
  },
  {
    key: "admin-MonitorOnIcon",
    currentName: "MonitorOnIcon",
    currentIcon: <MonitorOnIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "Unused, remove from admin-ui",
  },
  {
    key: "admin-NextArrow",
    currentName: "NextArrow",
    currentIcon: <NextArrow boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: "ChevronRight",
    notes: "Pagination",
  },
  {
    key: "admin-PrevArrow",
    currentName: "PrevArrow",
    currentIcon: <PrevArrow boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: "ChevronLeft",
    notes: "Pagination",
  },
  {
    key: "admin-RightArrow",
    currentName: "RightArrow",
    currentIcon: <RightArrow boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: "ArrowRight",
    notes: "",
  },
  {
    key: "admin-OktaLogoIcon",
    currentName: "OktaLogoIcon",
    currentIcon: <OktaLogoIcon />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "Brand logo, no Carbon equivalent",
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
    key: "admin-PlayIcon",
    currentName: "PlayIcon",
    currentIcon: <PlayIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "Unused, remove from admin-ui",
  },
  {
    key: "admin-SparkleIcon",
    currentName: "SparkleIcon",
    currentIcon: <AdminSparkleIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: "MagicWandFilled",
    notes: "Duplicate of fidesui version",
  },
  {
    key: "admin-DatabaseIcon",
    currentName: "DatabaseIcon",
    currentIcon: <DatabaseIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "Unused, remove from admin-ui",
  },
  {
    key: "admin-DatasetIcon",
    currentName: "DatasetIcon",
    currentIcon: <DatasetIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "Unused, remove from admin-ui",
  },
  {
    key: "admin-FieldIcon",
    currentName: "FieldIcon",
    currentIcon: <FieldIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "Unused, remove from admin-ui",
  },
  {
    key: "admin-TableIcon",
    currentName: "TableIcon",
    currentIcon: <DBTableIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "Unused, remove from admin-ui",
  },
  {
    key: "admin-RightDownArrowIcon",
    currentName: "RightDownArrowIcon",
    currentIcon: (
      <SvgIconBox>
        <RightDownArrowIcon width={20} height={20} />
      </SvgIconBox>
    ),
    iconType: "custom-svg",
    source: "admin-ui",
    suggestedCarbon: "ArrowDownRight",
    notes: "svg/ subdirectory",
  },
  {
    key: "admin-RightUpArrowIcon",
    currentName: "RightUpArrowIcon",
    currentIcon: (
      <SvgIconBox>
        <RightUpArrowIcon width={20} height={20} />
      </SvgIconBox>
    ),
    iconType: "custom-svg",
    source: "admin-ui",
    suggestedCarbon: "ArrowUpRight",
    notes: "svg/ subdirectory",
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
  {
    key: "admin-SlackIcon-chat",
    currentName: "SlackIcon (chat-provider)",
    currentIcon: <SlackIconChat />,
    iconType: "custom-svg",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "Brand logo, no Carbon equivalent",
  },
  {
    key: "admin-SlackIcon-assessments",
    currentName: "SlackIcon (privacy-assessments)",
    currentIcon: <AssessmentsSlackIcon />,
    iconType: "custom-svg",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "Brand logo, no Carbon equivalent",
  },
  {
    key: "admin-AwsIcon-messaging",
    currentName: "AwsIcon (messaging)",
    currentIcon: <AwsIcon />,
    iconType: "custom-svg",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "Brand logo, no Carbon equivalent",
  },
  {
    key: "admin-MailgunIcon",
    currentName: "MailgunIcon",
    currentIcon: <MailgunIcon />,
    iconType: "custom-svg",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "Brand logo, no Carbon equivalent",
  },
  {
    key: "admin-TwilioIcon",
    currentName: "TwilioIcon",
    currentIcon: <TwilioIcon />,
    iconType: "custom-svg",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "Brand logo, no Carbon equivalent",
  },
  {
    key: "admin-AddIcon-custom-fields",
    currentName: "AddIcon (custom-fields)",
    currentIcon: <CustomFieldsAddIcon boxSize={5} />,
    iconType: "createIcon",
    source: "admin-ui",
    suggestedCarbon: null,
    notes: "Unused, remove from admin-ui",
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
      const labels: Record<IconType, { text: string; color: string }> = {
        createIcon: { text: "createIcon", color: "corinth" },
        "chakra-icon": { text: "Chakra Icon", color: "olive" },
        "custom-svg": { text: "Custom SVG", color: "sandstone" },
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
