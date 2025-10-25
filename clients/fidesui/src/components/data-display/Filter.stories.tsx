import type { Meta, StoryObj } from "@storybook/react-vite";
import { Flex, Typography } from "antd";
import type { TreeProps } from "antd/lib";
import { notification as AntNotification } from "antd/lib";
import { useState } from "react";

import { Filter } from "./Filter";

const meta = {
  title: "DataDisplay/Filter",
  component: Filter,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  args: {
    treeProps: {
      treeData: [],
    },
  },
} satisfies Meta<typeof Filter>;

export default meta;
type Story = StoryObj<typeof meta>;

// Sample tree data matching the mockup structure
const sampleTreeData: TreeProps["treeData"] = [
  {
    title: "Status",
    key: "status",
    children: [
      { title: "Unlabeled", key: "status-unlabeled" },
      { title: "Classifying", key: "status-classifying" },
      { title: "In review", key: "status-in-review" },
      { title: "Approved", key: "status-approved" },
      { title: "Confirmed", key: "status-confirmed" },
      { title: "Ignored", key: "status-ignored" },
      { title: "Removed", key: "status-removed" },
    ],
  },
  {
    title: "Confidence",
    key: "confidence",
    children: [
      { title: "High", key: "confidence-high" },
      { title: "Low", key: "confidence-low" },
      { title: "User-applied", key: "confidence-user-applied" },
    ],
  },
  {
    title: "Data categories",
    key: "data-categories",
    children: [
      {
        title: "User data",
        key: "user-data",
        children: [
          { title: "Contact", key: "user-data-contact" },
          { title: "Demographic", key: "user-data-demographic" },
          { title: "Financial", key: "user-data-financial" },
        ],
      },
      {
        title: "System data",
        key: "system-data",
        children: [
          { title: "Operations", key: "system-data-operations" },
          { title: "Authentication", key: "system-data-authentication" },
        ],
      },
    ],
  },
];

export const Primary: Story = {
  args: {},
  render: (args) => {
    const initialCheckedKeys: React.Key[] = [
      "status-unlabeled",
      "status-classifying",
      "status-in-review",
      "status-approved",
      "status-removed",
    ];
    const initialExpandedKeys: React.Key[] = ["status"];

    const [checkedKeys, setCheckedKeys] =
      useState<React.Key[]>(initialCheckedKeys);
    const [expandedKeys, setExpandedKeys] =
      useState<React.Key[]>(initialExpandedKeys);

    const activeFiltersCount = checkedKeys.length;

    return (
      <Filter
        {...args}
        activeFiltersCount={activeFiltersCount}
        treeProps={{
          checkable: true,
          checkedKeys,
          onCheck: (checked) => {
            setCheckedKeys(checked as React.Key[]);
          },
          expandedKeys,
          onExpand: (expanded) => {
            setExpandedKeys(expanded as React.Key[]);
          },
          treeData: sampleTreeData,
        }}
        onApply={() => {
          AntNotification.success({
            message: "Filters applied",
            description: `${checkedKeys.length} filter(s) applied`,
            placement: "topRight",
          });
        }}
        onReset={() => {
          setCheckedKeys(initialCheckedKeys);
          setExpandedKeys(initialExpandedKeys);
          AntNotification.info({
            message: "Filters reset",
            description: "All filters have been reset to default",
            placement: "topRight",
          });
        }}
        onClear={() => {
          setCheckedKeys([]);
          AntNotification.info({
            message: "Filters cleared",
            description: "All selections have been cleared",
            placement: "topRight",
          });
        }}
      />
    );
  },
};

export const NoFiltersActive: Story = {
  args: {},
  render: () => {
    const initialCheckedKeys: React.Key[] = [];
    const initialExpandedKeys: React.Key[] = [];

    const [checkedKeys, setCheckedKeys] =
      useState<React.Key[]>(initialCheckedKeys);
    const [expandedKeys, setExpandedKeys] =
      useState<React.Key[]>(initialExpandedKeys);

    return (
      <Filter
        activeFiltersCount={checkedKeys.length}
        treeProps={{
          selectable: false,
          checkable: true,
          checkedKeys,
          onCheck: (checked) => {
            setCheckedKeys(checked as React.Key[]);
          },
          expandedKeys,
          onExpand: (expanded) => {
            setExpandedKeys(expanded as React.Key[]);
          },
          treeData: sampleTreeData,
        }}
        onApply={() => {
          AntNotification.success({
            message: "Filters applied",
            description: `${checkedKeys.length} filter(s) applied`,
            placement: "topRight",
          });
        }}
        onReset={() => {
          setCheckedKeys(initialCheckedKeys);
          setExpandedKeys(initialExpandedKeys);
          AntNotification.info({
            message: "Filters reset",
            description: "All filters have been reset to default",
            placement: "topRight",
          });
        }}
        onClear={() => {
          setCheckedKeys([]);
          AntNotification.info({
            message: "Filters cleared",
            description: "All selections have been cleared",
            placement: "topRight",
          });
        }}
      />
    );
  },
};

export const ControlledOpen: Story = {
  args: {},
  render: () => {
    const initialCheckedKeys: React.Key[] = ["status-approved"];
    const initialExpandedKeys: React.Key[] = ["status"];

    const [checkedKeys, setCheckedKeys] =
      useState<React.Key[]>(initialCheckedKeys);
    const [expandedKeys, setExpandedKeys] =
      useState<React.Key[]>(initialExpandedKeys);
    const [open, setOpen] = useState(true);

    return (
      <Flex vertical align="flex-end" gap="small">
        <Typography.Text>
          The popover is controlled and starts open
        </Typography.Text>
        <div>
          <Filter
            open={open}
            onOpenChange={setOpen}
            activeFiltersCount={checkedKeys.length}
            treeProps={{
              selectable: false,
              checkable: true,
              checkedKeys,
              onCheck: (checked) => {
                setCheckedKeys(checked as React.Key[]);
              },
              expandedKeys,
              onExpand: (expanded) => {
                setExpandedKeys(expanded as React.Key[]);
              },
              treeData: sampleTreeData,
            }}
            onApply={() => {
              setOpen(false);
              AntNotification.success({
                message: "Filters applied",
                description: `${checkedKeys.length} filter(s) applied`,
                placement: "topRight",
              });
            }}
            onReset={() => {
              setCheckedKeys(initialCheckedKeys);
              setExpandedKeys(initialExpandedKeys);
              AntNotification.info({
                message: "Filters reset",
                description: "All filters have been reset to default",
                placement: "topRight",
              });
            }}
            onClear={() => {
              setCheckedKeys([]);
              AntNotification.info({
                message: "Filters cleared",
                description: "All selections have been cleared",
                placement: "topRight",
              });
            }}
          />
        </div>
      </Flex>
    );
  },
};

export const WithSearch: Story = {
  args: {},
  render: () => {
    const initialCheckedKeys: React.Key[] = [];
    const initialExpandedKeys: React.Key[] = [];

    const [checkedKeys, setCheckedKeys] =
      useState<React.Key[]>(initialCheckedKeys);
    const [expandedKeys, setExpandedKeys] =
      useState<React.Key[]>(initialExpandedKeys);

    return (
      <Flex vertical align="flex-end" gap="small">
        <Typography.Text>
          Try searching for &quot;user&quot; or &quot;high&quot;
        </Typography.Text>
        <div>
          <Filter
            activeFiltersCount={checkedKeys.length}
            treeProps={{
              selectable: false,
              checkable: true,
              checkedKeys,
              onCheck: (checked) => {
                setCheckedKeys(checked as React.Key[]);
              },
              expandedKeys,
              onExpand: (expanded) => {
                setExpandedKeys(expanded as React.Key[]);
              },
              treeData: sampleTreeData,
            }}
            onApply={() => {
              AntNotification.success({
                message: "Filters applied",
                description: `${checkedKeys.length} filter(s) applied`,
                placement: "topRight",
              });
            }}
            onReset={() => {
              setCheckedKeys(initialCheckedKeys);
              setExpandedKeys(initialExpandedKeys);
              AntNotification.info({
                message: "Filters reset",
                description: "All filters have been reset to default",
                placement: "topRight",
              });
            }}
            onClear={() => {
              setCheckedKeys([]);
              AntNotification.info({
                message: "Filters cleared",
                description: "All selections have been cleared",
                placement: "topRight",
              });
            }}
          />
        </div>
      </Flex>
    );
  },
};

export const WithoutSearch: Story = {
  args: {},
  render: () => {
    const initialCheckedKeys: React.Key[] = [];
    const initialExpandedKeys: React.Key[] = [];

    const [checkedKeys, setCheckedKeys] =
      useState<React.Key[]>(initialCheckedKeys);
    const [expandedKeys, setExpandedKeys] =
      useState<React.Key[]>(initialExpandedKeys);

    return (
      <Flex vertical align="flex-end" gap="small">
        <Typography.Text>Search input is hidden</Typography.Text>
        <div>
          <Filter
            activeFiltersCount={checkedKeys.length}
            showSearch={false}
            treeProps={{
              selectable: false,
              checkable: true,
              checkedKeys,
              onCheck: (checked) => {
                setCheckedKeys(checked as React.Key[]);
              },
              expandedKeys,
              onExpand: (expanded) => {
                setExpandedKeys(expanded as React.Key[]);
              },
              treeData: sampleTreeData,
            }}
            onApply={() => {
              AntNotification.success({
                message: "Filters applied",
                description: `${checkedKeys.length} filter(s) applied`,
                placement: "topRight",
              });
            }}
            onReset={() => {
              setCheckedKeys(initialCheckedKeys);
              setExpandedKeys(initialExpandedKeys);
              AntNotification.info({
                message: "Filters reset",
                description: "All filters have been reset to default",
                placement: "topRight",
              });
            }}
            onClear={() => {
              setCheckedKeys([]);
              AntNotification.info({
                message: "Filters cleared",
                description: "All selections have been cleared",
                placement: "topRight",
              });
            }}
          />
        </div>
      </Flex>
    );
  },
};
