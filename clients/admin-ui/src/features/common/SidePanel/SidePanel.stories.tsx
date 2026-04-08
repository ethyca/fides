// @ts-expect-error — Storybook types are in fidesui, not admin-ui
import type { Meta, StoryObj } from "@storybook/react-vite";
import { configureStore } from "@reduxjs/toolkit";
import { Badge, Button, Checkbox, Icons, Select, Typography } from "fidesui";
import React, { useState } from "react";
import { Provider } from "react-redux";

import { reducer as sidePanelReducer } from "./sidepanel.slice";
import SidePanel from "./SidePanel";
import { SidePanelProvider } from "./SidePanelContext";

const { Text } = Typography;

// Minimal store with just the sidePanel slice for stories
const storyStore = configureStore({
  reducer: {
    sidePanel: sidePanelReducer,
  },
});

const meta = {
  title: "Admin UI/SidePanel",
  decorators: [
    (Story: React.FC) => (
      <Provider store={storyStore}>
        <SidePanelProvider>
          <div
            style={{
              display: "flex",
              height: "100vh",
              background: "#f5f5f5",
            }}
          >
            {/* Rail placeholder */}
            <div
              style={{
                width: 56,
                flexShrink: 0,
                background: "#1a1a2e",
              }}
            />
            <Story />
            {/* Content area placeholder */}
            <div
              style={{
                flex: 1,
                padding: 24,
                background: "#fff",
                overflow: "auto",
              }}
            >
              <Text type="secondary">Content area</Text>
            </div>
          </div>
        </SidePanelProvider>
      </Provider>
    ),
  ],
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

// Story 1: List page (e.g., Systems)
const ListPagePanel = () => {
  const [searchValue, setSearchValue] = useState("");
  const [selectedCount] = useState(3);
  const [filterGroup, setFilterGroup] = useState<string | undefined>(undefined);
  const [filterStatus, setFilterStatus] = useState<string | undefined>(
    undefined,
  );

  const activeFilterCount = [filterGroup, filterStatus].filter(Boolean).length;

  return (
    <SidePanel>
      <SidePanel.Identity
        title="Systems"
        description="Manage registered systems in your organization"
      />
      <SidePanel.Search
        placeholder="Search systems..."
        onSearch={(v) => setSearchValue(v)}
        value={searchValue}
        onChange={(e) => setSearchValue(e.target.value)}
      />
      <SidePanel.Actions>
        <Button type="primary" icon={<Icons.Add />}>
          Add system
        </Button>
        {selectedCount > 0 && (
          <>
            <Badge count={selectedCount} size="small">
              <Text type="secondary" style={{ fontSize: 12 }}>
                selected
              </Text>
            </Badge>
            <Button size="small">Bulk edit</Button>
            <Button size="small" danger>
              Delete selected
            </Button>
          </>
        )}
      </SidePanel.Actions>
      <SidePanel.Filters
        activeCount={activeFilterCount}
        onClearAll={() => {
          setFilterGroup(undefined);
          setFilterStatus(undefined);
        }}
      >
        <div>
          <Text type="secondary" style={{ fontSize: 12, display: "block" }}>
            Group
          </Text>
          <Select
            placeholder="All groups"
            style={{ width: "100%" }}
            value={filterGroup}
            onChange={setFilterGroup}
            allowClear
            options={[
              { value: "marketing", label: "Marketing" },
              { value: "engineering", label: "Engineering" },
              { value: "sales", label: "Sales" },
            ]}
          />
        </div>
        <div>
          <Text type="secondary" style={{ fontSize: 12, display: "block" }}>
            Status
          </Text>
          <Select
            placeholder="All statuses"
            style={{ width: "100%" }}
            value={filterStatus}
            onChange={setFilterStatus}
            allowClear
            options={[
              { value: "active", label: "Active" },
              { value: "draft", label: "Draft" },
              { value: "archived", label: "Archived" },
            ]}
          />
        </div>
        <div>
          <Text type="secondary" style={{ fontSize: 12, display: "block" }}>
            Data steward
          </Text>
          <Select
            placeholder="All stewards"
            style={{ width: "100%" }}
            allowClear
            options={[
              { value: "alice", label: "Alice" },
              { value: "bob", label: "Bob" },
            ]}
          />
        </div>
      </SidePanel.Filters>
    </SidePanel>
  );
};

export const ListPage: Story = {
  render: () => <ListPagePanel />,
};

// Story 2: Detail page (e.g., System Detail)
const DetailPagePanel = () => {
  const [activeTab, setActiveTab] = useState("info");

  return (
    <SidePanel>
      <SidePanel.Identity
        title="Acme Analytics"
        breadcrumbItems={[
          { title: "Systems", href: "/systems" },
          { title: "Acme Analytics" },
        ]}
        description="Third-party analytics platform"
      />
      <SidePanel.Navigation
        items={[
          { key: "info", label: "Information" },
          { key: "data-uses", label: "Data uses" },
          { key: "data-flow", label: "Data flow" },
          { key: "assets", label: "Assets" },
          { key: "history", label: "History" },
        ]}
        activeKey={activeTab}
        onSelect={setActiveTab}
      />
      <SidePanel.Actions>
        <Button type="primary">Save</Button>
        <Button danger>Delete system</Button>
      </SidePanel.Actions>
    </SidePanel>
  );
};

export const DetailPage: Story = {
  render: () => <DetailPagePanel />,
};

// Story 3: Settings page with grouped navigation
const SettingsPagePanel = () => {
  const [activeKey, setActiveKey] = useState("organization");

  return (
    <SidePanel>
      <SidePanel.Identity title="Settings" />
      <SidePanel.Navigation
        items={[
          {
            key: "platform",
            label: "Platform",
            type: "group",
            children: [
              { key: "organization", label: "Organization" },
              { key: "users", label: "Users" },
              { key: "roles", label: "Roles" },
              { key: "notifications", label: "Notifications" },
              { key: "custom-fields", label: "Custom fields" },
            ],
          },
          {
            key: "governance",
            label: "Governance",
            type: "group",
            children: [
              { key: "taxonomy", label: "Taxonomy" },
              { key: "locations", label: "Locations & Regulations" },
            ],
          },
          { key: "about", label: "About Fides" },
        ]}
        activeKey={activeKey}
        onSelect={setActiveKey}
      />
      <SidePanel.ViewSettings defaultOpen>
        <Checkbox.Group
          options={[
            { label: "Name", value: "name" },
            { label: "Email", value: "email" },
            { label: "Role", value: "role" },
            { label: "Created", value: "created" },
            { label: "Last login", value: "lastLogin" },
          ]}
          defaultValue={["name", "email", "role"]}
          style={{ display: "flex", flexDirection: "column", gap: 4 }}
        />
      </SidePanel.ViewSettings>
    </SidePanel>
  );
};

export const SettingsPage: Story = {
  render: () => <SettingsPagePanel />,
};
