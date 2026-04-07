import {
  DataBase,
  Edit,
  Locked,
  Policy,
  Screen,
  SettingsCheck,
} from "@carbon/icons-react";
import type { CarbonIconType } from "@carbon/icons-react";
import {
  Avatar,
  Button,
  Card,
  Col,
  Collapse,
  Divider,
  Flex,
  Form,
  Input,
  Modal,
  Progress,
  Row,
  Select,
  Switch,
  Tabs,
  Tag,
  Text,
  Title,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useState } from "react";

import type { MockSystem } from "../types";
import { SystemCapability } from "../types";
import { getSystemCapabilities } from "../utils";

const CAPABILITY_ICONS: Record<SystemCapability, CarbonIconType> = {
  [SystemCapability.DSAR]: Locked,
  [SystemCapability.MONITORING]: Screen,
  [SystemCapability.CONSENT]: Policy,
  [SystemCapability.INTEGRATIONS]: SettingsCheck,
  [SystemCapability.CLASSIFICATION]: DataBase,
};
import ProducerConsumerCard from "../detail/cards/ProducerConsumerCard";

interface SystemDetailContentProps {
  system: MockSystem;
}

const SectionHeader = ({ title }: { title: string }) => (
  <>
    <Title level={4} className="!mb-0 !mt-0">{title}</Title>
    <Divider className="!mb-4 !mt-2" />
  </>
);

// --- About: symmetric two-column grid ---

const AboutField = ({ label, children }: { label: string; children: React.ReactNode }) => (
  <div className="min-h-[42px]">
    <Text type="secondary" className="mb-1 block text-[10px] uppercase tracking-wider">{label}</Text>
    <Text strong className="block text-sm">{children}</Text>
  </div>
);

const AboutSection = ({ system }: { system: MockSystem }) => {
  const [editing, setEditing] = useState(false);

  return (
    <div>
      <Flex justify="space-between" align="center">
        <Title level={4} className="!mb-0 !mt-0">About</Title>
        <Button type="text" size="small" icon={<Edit size={14} />} onClick={() => setEditing(true)}>Edit</Button>
      </Flex>
      <Divider className="!mb-4 !mt-2" />

      <Row gutter={[32, 16]}>
        <Col span={12}><AboutField label="Type">{system.system_type}</AboutField></Col>
        <Col span={12}><AboutField label="Responsibility">{system.responsibility}</AboutField></Col>
        <Col span={12}><AboutField label="Department">{system.department}</AboutField></Col>
        <Col span={12}>
          <AboutField label="Roles">
            {system.roles.length > 0
              ? system.roles.map((r) => r.charAt(0).toUpperCase() + r.slice(1)).join(", ")
              : "—"}
          </AboutField>
        </Col>
        <Col span={12}><AboutField label="Group">{system.group ?? "—"}</AboutField></Col>
        <Col span={12}><AboutField label="Description">{system.description}</AboutField></Col>
      </Row>

      <Modal title="Edit system details" open={editing} onCancel={() => setEditing(false)} onOk={() => setEditing(false)} okText="Save" width={600}>
        <Flex vertical gap={16} className="mt-4">
          <div><Text type="secondary" className="mb-1 block text-xs">System type</Text><Input defaultValue={system.system_type} /></div>
          <div><Text type="secondary" className="mb-1 block text-xs">Department</Text><Input defaultValue={system.department} /></div>
          <div><Text type="secondary" className="mb-1 block text-xs">Responsibility</Text><Select defaultValue={system.responsibility} className="w-full" options={[{label:"Controller",value:"Controller"},{label:"Processor",value:"Processor"},{label:"Sub-Processor",value:"Sub-Processor"}]} /></div>
          <div><Text type="secondary" className="mb-1 block text-xs">Group</Text><Input defaultValue={system.group ?? ""} /></div>
          <div><Text type="secondary" className="mb-1 block text-xs">Roles</Text><Select mode="multiple" defaultValue={system.roles} className="w-full" options={[{label:"Producer",value:"producer"},{label:"Consumer",value:"consumer"}]} /></div>
          <div><Text type="secondary" className="mb-1 block text-xs">Description</Text><Input.TextArea rows={3} defaultValue={system.description} /></div>
        </Flex>
      </Modal>
    </div>
  );
};

// --- Governance cards ---

const PurposesSection = ({ system }: { system: MockSystem }) => (
  <Card size="small" className="h-full" title={<Text strong className="text-sm">Purposes</Text>} extra={<Button type="text" size="small">+ Add</Button>}>
    {system.purposes.length > 0 ? (
      <Flex gap={6} wrap>
        {system.purposes.map((p) => (
          <Tag key={p.name} bordered={false} style={{ backgroundColor: palette.FIDESUI_NEUTRAL_100 }}>{p.name}</Tag>
        ))}
      </Flex>
    ) : (
      <Text type="secondary" className="text-xs">No purposes defined</Text>
    )}
  </Card>
);

const StewardsSection = ({ system }: { system: MockSystem }) => (
  <Card size="small" className="h-full" title={<Text strong className="text-sm">Stewards</Text>} extra={<Button type="text" size="small">+ Add</Button>}>
    {system.stewards.length > 0 ? (
      <Flex vertical gap={8}>
        {system.stewards.map((st) => (
          <Flex key={st.initials} align="center" gap={8}>
            <Avatar size={24} style={{ backgroundColor: "#e6e6e8", color: "#53575c", fontSize: 10 }}>{st.initials}</Avatar>
            <Text className="text-xs">{st.name}</Text>
          </Flex>
        ))}
      </Flex>
    ) : (
      <Text type="secondary" className="text-xs">No steward assigned</Text>
    )}
  </Card>
);

const CapabilitiesSection = ({ system }: { system: MockSystem }) => {
  const capabilities = getSystemCapabilities(system);
  return (
    <Card size="small" className="h-full" title={<Text strong className="text-sm">Capabilities</Text>}>
      {capabilities.length > 0 ? (
        <Flex vertical gap={8}>
          <Flex gap={6} wrap>
            {capabilities.map((cap) => {
              const Icon = CAPABILITY_ICONS[cap];
              return (
                <Tag key={cap} bordered={false} style={{ backgroundColor: palette.FIDESUI_NEUTRAL_100 }}>
                  <Flex align="center" gap={4}>
                    <Icon size={12} />
                    {cap}
                  </Flex>
                </Tag>
              );
            })}
          </Flex>
          <Text type="secondary" className="text-[10px]">Based on active integrations</Text>
        </Flex>
      ) : (
        <Text type="secondary" className="text-xs">No capabilities detected</Text>
      )}
    </Card>
  );
};

// --- Classification (compact with mini metric cards) ---

const MiniMetric = ({ label, value }: { label: string; value: number }) => (
  <div className="rounded-md px-3 py-2" style={{ backgroundColor: palette.FIDESUI_CORINTH }}>
    <Text type="secondary" className="block text-[10px] uppercase tracking-wider">{label}</Text>
    <Text strong className="text-lg">{value}</Text>
  </div>
);

const ClassificationSection = ({ system }: { system: MockSystem }) => {
  const { approved, pending, unreviewed, categories } = system.classification;
  const total = approved + pending + unreviewed;

  return (
    <Card size="small" title={<Text strong className="text-sm">Classification Progress</Text>} extra={<Text className="cursor-pointer text-xs" style={{ color: palette.FIDESUI_MINOS }}>Review fields &rarr;</Text>}>
      <Row gutter={24}>
        {/* Col 1: Progress bar */}
        <Col span={8}>
          {total > 0 && (
            <Flex vertical gap={8}>
              <Flex className="h-[10px] w-full overflow-hidden rounded-full">
                <div style={{ width: `${(approved / total) * 100}%`, backgroundColor: "#5a9a68" }} />
                <div style={{ width: `${(pending / total) * 100}%`, backgroundColor: "#4a90e2" }} />
                <div style={{ width: `${(unreviewed / total) * 100}%`, backgroundColor: "#e6e6e8" }} />
              </Flex>
              <Flex vertical gap={3}>
                <Flex align="center" gap={4}>
                  <div className="size-[6px] rounded-full" style={{ backgroundColor: "#5a9a68" }} />
                  <Text className="text-[10px]">{approved} approved</Text>
                </Flex>
                <Flex align="center" gap={4}>
                  <div className="size-[6px] rounded-full" style={{ backgroundColor: "#4a90e2" }} />
                  <Text className="text-[10px]">{pending} classified</Text>
                </Flex>
                <Flex align="center" gap={4}>
                  <div className="size-[6px] rounded-full" style={{ backgroundColor: "#e6e6e8" }} />
                  <Text className="text-[10px]">{unreviewed} unlabeled</Text>
                </Flex>
              </Flex>
            </Flex>
          )}
        </Col>

        {/* Col 2: Monitors */}
        <Col span={8} className="border-l border-solid border-[#f0f0f0] pl-6">
          <Text strong className="mb-2 block text-[10px] uppercase tracking-wider">Monitors</Text>
          {system.monitors.length > 0 ? (
            <Flex vertical gap={4}>
              {system.monitors.map((mon) => (
                <Flex key={mon.name} justify="space-between" align="center">
                  <Text className="text-xs">{mon.name}</Text>
                  <Flex align="center" gap={6}>
                    <Text type="secondary" className="text-[10px]">{mon.resourceCount}</Text>
                    <Tag color={mon.status === "completed" ? "success" : mon.status === "failed" ? "error" : "warning"} bordered={false} className="!text-[9px]">{mon.status}</Tag>
                  </Flex>
                </Flex>
              ))}
            </Flex>
          ) : (
            <Text type="secondary" className="text-xs">No monitors</Text>
          )}
        </Col>

        {/* Col 3: Categories */}
        <Col span={8} className="border-l border-solid border-[#f0f0f0] pl-6">
          <Text strong className="mb-2 block text-[10px] uppercase tracking-wider">Categories</Text>
          {categories.length > 0 ? (
            <Flex vertical gap={4}>
              {categories.map((cat) => (
                <Flex key={cat.name} justify="space-between" align="center">
                  <Text className="text-xs">{cat.name}</Text>
                  <Flex align="center" gap={6}>
                    <Text type="secondary" className="text-[10px]">{cat.fieldCount} fields</Text>
                    <Text strong className="text-xs">{cat.approvedPercent}%</Text>
                  </Flex>
                </Flex>
              ))}
            </Flex>
          ) : (
            <Text type="secondary" className="text-xs">No categories</Text>
          )}
        </Col>
      </Row>
    </Card>
  );
};

// --- Datasets section (searchable/filterable table) ---

const DatasetsSection = ({ system }: { system: MockSystem }) => {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [yamlOpen, setYamlOpen] = useState<string | null>(null);

  const filtered = system.datasets.filter((ds) => {
    if (search) {
      const q = search.toLowerCase();
      if (!ds.name.toLowerCase().includes(q) && !ds.key.toLowerCase().includes(q) && !(ds.category?.toLowerCase().includes(q))) return false;
    }
    if (statusFilter && ds.status !== statusFilter) return false;
    return true;
  });

  const statuses = [...new Set(system.datasets.map((d) => d.status).filter(Boolean))];

  return (
    <Flex vertical gap={12}>
      <Flex justify="space-between" align="center">
        <Input
          placeholder="Search datasets..."
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearch(e.target.value)}
          allowClear
          size="small"
          style={{ width: 240 }}
        />
        <Flex gap={8} align="center">
          <Select
            placeholder="All statuses"
            value={statusFilter}
            onChange={setStatusFilter}
            allowClear
            size="small"
            className="w-[140px]"
            options={statuses.map((s) => ({ label: s!.charAt(0).toUpperCase() + s!.slice(1), value: s! }))}
          />
          <Text type="secondary" className="text-xs">{filtered.length} datasets</Text>
        </Flex>
      </Flex>

      <Flex vertical gap={0}>
        <Flex className="border-b border-solid border-[#f0f0f0] px-3 py-2" style={{ backgroundColor: palette.FIDESUI_CORINTH }}>
          <Text strong className="w-[20%] text-[10px] uppercase tracking-wider">Dataset</Text>
          <Text strong className="w-[14%] text-[10px] uppercase tracking-wider">Category</Text>
          <Text strong className="w-[10%] text-[10px] uppercase tracking-wider">Status</Text>
          <Text strong className="w-[10%] text-[10px] uppercase tracking-wider">Collections</Text>
          <Text strong className="w-[10%] text-[10px] uppercase tracking-wider">Fields</Text>
          <Text strong className="w-[16%] text-[10px] uppercase tracking-wider">Usage</Text>
          <Text strong className="w-[10%] text-[10px] uppercase tracking-wider">Created</Text>
          <Text strong className="w-[10%] text-right text-[10px] uppercase tracking-wider">Actions</Text>
        </Flex>
        {filtered.map((ds) => (
          <Flex key={ds.key} align="center" className="border-b border-solid border-[#f5f5f5] px-3 py-2">
            <Flex vertical className="w-[20%]">
              <Text className="text-xs">{ds.name}</Text>
              <Text type="secondary" className="text-[10px]">{ds.key}</Text>
            </Flex>
            <div className="w-[14%]">
              {ds.category ? (
                <Tag bordered={false} style={{ backgroundColor: palette.FIDESUI_NEUTRAL_100 }} className="!text-[10px]">{ds.category}</Tag>
              ) : (
                <Text type="secondary" className="text-[10px]">—</Text>
              )}
            </div>
            <div className="w-[10%]">
              <Tag
                color={ds.status === "approved" ? "success" : ds.status === "pending" ? "warning" : "default"}
                bordered={false}
                className="!text-[9px]"
              >
                {ds.status ?? "—"}
              </Tag>
            </div>
            <Text type="secondary" className="w-[10%] text-xs">{ds.collectionCount}</Text>
            <Text type="secondary" className="w-[10%] text-xs">{ds.fieldCount.toLocaleString()}</Text>
            <div className="w-[16%]">
              {ds.usage ? (
                <Flex gap={4} wrap>
                  {ds.usage.split(", ").map((u) => (
                    <Tag key={u} bordered={false} style={{ backgroundColor: palette.FIDESUI_NEUTRAL_100 }} className="!text-[9px]">{u}</Tag>
                  ))}
                </Flex>
              ) : (
                <Text type="secondary" className="text-[10px]">—</Text>
              )}
            </div>
            <Text type="secondary" className="w-[10%] text-[10px]">{ds.createdAt}</Text>
            <Flex className="w-[10%]" justify="flex-end" gap={6}>
              <Button size="small" type="default" className="!text-[10px]" onClick={() => setYamlOpen(yamlOpen === ds.key ? null : ds.key)}>
                YAML
              </Button>
            </Flex>
          </Flex>
        ))}
        {filtered.length === 0 && (
          <Flex justify="center" className="py-6">
            <Text type="secondary" className="text-xs">No datasets match filters</Text>
          </Flex>
        )}
      </Flex>

      {yamlOpen && (
        <Card size="small" title={<Text strong className="text-xs">YAML — {yamlOpen}</Text>} extra={<Button type="text" size="small" onClick={() => setYamlOpen(null)}>Close</Button>}>
          <pre className="overflow-auto rounded bg-[#2b2e35] p-3 text-[11px] text-[#f5f5f5]">
{`dataset:
  fides_key: ${yamlOpen}
  name: ${system.datasets.find((d) => d.key === yamlOpen)?.name}
  collections:
    - name: users
      fields:
        - name: email
          data_categories: [user.contact.email]
        - name: name
          data_categories: [user.name]
        - name: phone
          data_categories: [user.contact.phone_number]`}
          </pre>
        </Card>
      )}
    </Flex>
  );
};

// --- Integrations (with Scopes header + button actions) ---

const IntegrationsSection = ({ system }: { system: MockSystem }) => (
  <div>
    <Flex justify="space-between" align="center" className="mb-3">
      <Text strong className="text-sm">Integrations</Text>
      <Button type="primary" size="small">+ Add</Button>
    </Flex>
    {system.integrations.length > 0 ? (
      <Flex vertical gap={0}>
        <Flex className="border-b border-solid border-[#f0f0f0] px-3 py-2" style={{ backgroundColor: palette.FIDESUI_CORINTH }}>
          <Text strong className="w-[28%] text-[10px] uppercase tracking-wider">Name</Text>
          <Text strong className="w-[14%] text-[10px] uppercase tracking-wider">Type</Text>
          <Text strong className="w-[12%] text-[10px] uppercase tracking-wider">Status</Text>
          <Text strong className="w-[16%] text-[10px] uppercase tracking-wider">Last tested</Text>
          <Text strong className="w-[15%] text-[10px] uppercase tracking-wider">Scopes</Text>
          <Text strong className="w-[15%] text-right text-[10px] uppercase tracking-wider">Actions</Text>
        </Flex>
        {system.integrations.map((intg) => (
          <Flex key={intg.name} align="center" className="border-b border-solid border-[#f5f5f5] px-3 py-2.5">
            <Text className="w-[28%] text-xs">{intg.name}</Text>
            <Text type="secondary" className="w-[14%] text-xs">{intg.type}</Text>
            <div className="w-[12%]">
              <Tag color={intg.status === "active" ? "success" : intg.status === "failed" ? "error" : intg.status === "untested" ? "warning" : "default"} bordered={false} className="!text-[10px]">{intg.status}</Tag>
            </div>
            <Text type="secondary" className="w-[16%] text-xs">{intg.lastTested ? new Date(intg.lastTested).toLocaleDateString() : "—"}</Text>
            <Text type="secondary" className="w-[15%] text-xs">{intg.enabledActions.join(", ")}</Text>
            <Flex className="w-[15%]" justify="flex-end" gap={6}>
              <Button size="small" type="default" className="!text-[11px]">Edit</Button>
              <Button size="small" type="default" className="!text-[11px]">Test</Button>
            </Flex>
          </Flex>
        ))}
      </Flex>
    ) : (
      <Text type="secondary" className="text-xs">No integrations configured</Text>
    )}
  </div>
);

// --- Activity (with colored status dots) ---

// --- History Tab (GRC audit log) ---

const CATEGORY_TAG_COLORS: Record<string, "sandstone" | "nectar" | "olive" | "minos" | "default"> = {
  classification: "sandstone",
  steward: "nectar",
  integration: "olive",
  purpose: "minos",
  system: "default",
};

const HistoryContent = ({ system }: { system: MockSystem }) => {
  const [categoryFilter, setCategoryFilter] = useState<string[]>([]);
  const [userFilter, setUserFilter] = useState<string[]>([]);
  const [search, setSearch] = useState("");

  const categories = [...new Set(system.history.map((e) => e.category))].sort();
  const users = [...new Set(system.history.map((e) => e.user))].sort();

  const filtered = system.history.filter((entry) => {
    if (categoryFilter.length > 0 && !categoryFilter.includes(entry.category)) return false;
    if (userFilter.length > 0 && !userFilter.includes(entry.user)) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!entry.action.toLowerCase().includes(q) && !entry.detail.toLowerCase().includes(q) && !(entry.fieldName?.toLowerCase().includes(q))) return false;
    }
    return true;
  });

  return (
    <Flex vertical gap={12}>
      {/* Search + Filters */}
      <Flex justify="space-between" align="center">
        <Input
          placeholder="Search history..."
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearch(e.target.value)}
          allowClear
          size="small"
          style={{ width: 260 }}
        />
        <Flex gap={12} align="center">
          <Select
            mode="multiple"
            placeholder="All categories"
            value={categoryFilter}
            onChange={setCategoryFilter}
            allowClear
            className="w-[180px]"
            size="small"
            options={categories.map((c) => ({ label: c.charAt(0).toUpperCase() + c.slice(1), value: c }))}
          />
          <Select
            mode="multiple"
            placeholder="All users"
            value={userFilter}
            onChange={setUserFilter}
            allowClear
            className="w-[180px]"
            size="small"
            options={users.map((u) => ({ label: u, value: u }))}
          />
          <Text type="secondary" className="text-xs">{filtered.length} entries</Text>
        </Flex>
      </Flex>

      {/* Table */}
      <div className="max-h-[700px] overflow-y-auto">
        {/* Header */}
        <Flex className="sticky top-0 z-10 border-b border-solid border-[#f0f0f0] px-3 py-2" style={{ backgroundColor: palette.FIDESUI_CORINTH }}>
          <Text strong className="w-[12%] text-[10px] uppercase tracking-wider">Date</Text>
          <Text strong className="w-[10%] text-[10px] uppercase tracking-wider">Category</Text>
          <Text strong className="w-[14%] text-[10px] uppercase tracking-wider">Action</Text>
          <Text strong className="w-[10%] text-[10px] uppercase tracking-wider">User</Text>
          <Text strong className="w-[12%] text-[10px] uppercase tracking-wider">Field</Text>
          <Text strong className="w-[18%] text-[10px] uppercase tracking-wider">Change</Text>
          <Text strong className="w-[24%] text-[10px] uppercase tracking-wider">Reason</Text>
        </Flex>

        {/* Rows */}
        {filtered.map((entry, i) => (
          <Flex key={i} align="center" className="border-b border-solid border-[#f5f5f5] px-3 py-2">
            <Text type="secondary" className="w-[12%] text-[10px]">
              {new Date(entry.timestamp).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
            </Text>
            <div className="w-[10%]">
              <Tag color={CATEGORY_TAG_COLORS[entry.category] ?? "default"} bordered={false} className="!text-[9px]">
                {entry.category}
              </Tag>
            </div>
            <Text className="w-[14%] text-xs">{entry.action}</Text>
            <Flex align="center" gap={4} className="w-[10%]">
              <Avatar size={18} style={{ backgroundColor: "#e6e6e8", color: "#53575c", fontSize: 8 }}>
                {entry.user.slice(0, 2).toUpperCase()}
              </Avatar>
              <Text className="text-[10px]">{entry.user.split(" ")[0]}</Text>
            </Flex>
            <Text type="secondary" className="w-[12%] truncate text-[10px]" title={entry.fieldName}>
              {entry.fieldName ?? "—"}
            </Text>
            <div className="w-[18%]">
              {entry.oldValue ? (
                <Text className="text-[10px]">
                  <Text type="secondary" className="text-[10px]" delete>{entry.oldValue}</Text>
                  {" → "}
                  <Text strong className="text-[10px]">{entry.newValue}</Text>
                </Text>
              ) : entry.newValue ? (
                <Text strong className="text-[10px]">{entry.newValue}</Text>
              ) : (
                <Text type="secondary" className="text-[10px]">—</Text>
              )}
            </div>
            <Text type="secondary" className="w-[24%] truncate text-[10px]" title={entry.reason}>
              {entry.reason ?? "—"}
            </Text>
          </Flex>
        ))}

        {filtered.length === 0 && (
          <Flex justify="center" className="py-8">
            <Text type="secondary" className="text-xs">No entries match the current filters</Text>
          </Flex>
        )}
      </div>
    </Flex>
  );
};

// --- Assets ---

const AssetsContent = ({ system }: { system: MockSystem }) => (
  <div>
    {system.datasets.length > 0 ? (
      <Flex vertical gap={0}>
        <Flex className="border-b border-solid border-[#f0f0f0] px-3 py-2" style={{ backgroundColor: palette.FIDESUI_CORINTH }}>
          <Text strong className="w-[30%] text-[10px] uppercase tracking-wider">Dataset</Text>
          <Text strong className="w-[20%] text-[10px] uppercase tracking-wider">Key</Text>
          <Text strong className="w-[15%] text-[10px] uppercase tracking-wider">Collections</Text>
          <Text strong className="w-[15%] text-[10px] uppercase tracking-wider">Fields</Text>
          <Text strong className="w-[20%] text-[10px] uppercase tracking-wider">Created</Text>
        </Flex>
        {system.datasets.map((ds) => (
          <Flex key={ds.key} align="center" className="border-b border-solid border-[#f5f5f5] px-3 py-2">
            <Text className="w-[30%] text-xs">{ds.name}</Text>
            <Text type="secondary" className="w-[20%] text-xs">{ds.key}</Text>
            <Text type="secondary" className="w-[15%] text-xs">{ds.collectionCount}</Text>
            <Text type="secondary" className="w-[15%] text-xs">{ds.fieldCount}</Text>
            <Text type="secondary" className="w-[20%] text-xs">{ds.createdAt}</Text>
          </Flex>
        ))}
      </Flex>
    ) : (
      <Text type="secondary" className="text-xs">No datasets linked</Text>
    )}
  </div>
);

// --- Advanced Tab ---

const AdvancedContent = ({ system }: { system: MockSystem }) => (
  <Form layout="vertical" initialValues={{ name: system.name, fides_key: system.fides_key, description: system.description, system_type: system.system_type, department: system.department, responsibility: system.responsibility, group: system.group ?? "", roles: system.roles, stewards: system.stewards.map((s) => s.name), purposes: system.purposes.map((p) => p.name) }}>
    <Collapse defaultActiveKey={["processing"]} accordion items={[
      { key: "processing", label: "Data Processing Properties", children: (
        <Flex vertical gap={16}>
          <Flex justify="space-between" align="center"><Text className="text-sm">Processes personal data</Text><Switch defaultChecked /></Flex>
          <Flex justify="space-between" align="center"><Text className="text-sm">Exempt from privacy regulations</Text><Switch /></Flex>
          <div><Text type="secondary" className="mb-1 block text-xs">Reason for exemption</Text><Input placeholder="Enter reason..." /></div>
          <Flex justify="space-between" align="center"><Text className="text-sm">Uses profiling</Text><Switch /></Flex>
          <div><Text type="secondary" className="mb-1 block text-xs">Legal basis for profiling</Text><Select mode="multiple" className="w-full" placeholder="Select..." options={[{label:"Consent",value:"consent"},{label:"Contract",value:"contract"},{label:"Legal obligation",value:"legal_obligation"},{label:"Vital interests",value:"vital_interests"},{label:"Public interest",value:"public_interest"},{label:"Legitimate interests",value:"legitimate_interests"}]} /></div>
          <Flex justify="space-between" align="center"><Text className="text-sm">Does international transfers</Text><Switch /></Flex>
          <div><Text type="secondary" className="mb-1 block text-xs">Legal basis for transfers</Text><Select mode="multiple" className="w-full" placeholder="Select..." options={[{label:"Adequacy decision",value:"adequacy"},{label:"SCCs",value:"sccs"},{label:"BCRs",value:"bcrs"},{label:"Derogations",value:"derogations"}]} /></div>
          <Flex justify="space-between" align="center"><Text className="text-sm">Requires data protection assessments</Text><Switch /></Flex>
          <div><Text type="secondary" className="mb-1 block text-xs">DPIA/DPA location</Text><Input placeholder="URL or file path..." /></div>
        </Flex>
      )},
      { key: "cookies", label: "Cookie Properties", children: (
        <Flex vertical gap={16}>
          <Flex justify="space-between" align="center"><Text className="text-sm">Uses cookies</Text><Switch /></Flex>
          <Flex justify="space-between" align="center"><Text className="text-sm">Refreshes cookies</Text><Switch /></Flex>
          <Flex justify="space-between" align="center"><Text className="text-sm">Uses non-cookie trackers</Text><Switch /></Flex>
          <div><Text type="secondary" className="mb-1 block text-xs">Cookie max age (seconds)</Text><Input type="number" placeholder="e.g. 31536000" /></div>
        </Flex>
      )},
      { key: "admin", label: "Administrative Properties", children: (
        <Flex vertical gap={16}>
          <div><Text type="secondary" className="mb-1 block text-xs">Privacy policy URL</Text><Input placeholder="https://..." /></div>
          <div><Text type="secondary" className="mb-1 block text-xs">Legal name</Text><Input placeholder="Legal entity name..." /></div>
          <div><Text type="secondary" className="mb-1 block text-xs">Legal address</Text><Input.TextArea rows={2} placeholder="Full legal address..." /></div>
          <div><Text type="secondary" className="mb-1 block text-xs">Legal contact / DPO</Text><Input placeholder="Contact name or email..." /></div>
          <div><Text type="secondary" className="mb-1 block text-xs">Joint controller info</Text><Input placeholder="Joint controller details..." /></div>
          <div><Text type="secondary" className="mb-1 block text-xs">Data security practices</Text><Input.TextArea rows={2} placeholder="Describe security measures..." /></div>
          <div><Text type="secondary" className="mb-1 block text-xs">Legitimate interest disclosure URL</Text><Input placeholder="https://..." /></div>
        </Flex>
      )},
      { key: "datasets", label: "Dataset References", children: (
        <div><Text type="secondary" className="mb-2 block text-xs">Link datasets to this system</Text><Select mode="multiple" className="w-full" placeholder="Select datasets..." options={system.datasets.map((d) => ({label:d.name,value:d.key}))} /></div>
      )},
      { key: "tags", label: "Tags & Custom Fields", children: (
        <Flex vertical gap={16}>
          <div><Text type="secondary" className="mb-1 block text-xs">System tags</Text><Select mode="tags" className="w-full" placeholder="Add tags..." /></div>
          <Text type="secondary" className="text-xs">Custom fields will appear here once the system is saved.</Text>
        </Flex>
      )},
    ]} />
    <Flex gap={8} justify="flex-end" className="mt-4">
      <Button>Cancel</Button>
      <Button type="primary">Save changes</Button>
    </Flex>
  </Form>
);

// --- Main ---

const SystemDetailContent = ({ system }: SystemDetailContentProps) => {
  const overviewContent = (
    <Flex vertical gap={40}>
      <AboutSection system={system} />
      <div>
        <SectionHeader title="Governance" />
        <Row gutter={[16, 16]}>
          <Col span={8}><PurposesSection system={system} /></Col>
          <Col span={8}><StewardsSection system={system} /></Col>
          <Col span={8}><CapabilitiesSection system={system} /></Col>
        </Row>
      </div>
      <div>
        <SectionHeader title="Classification" />
        <ClassificationSection system={system} />
      </div>
      <div>
        <SectionHeader title="Connections & Data Flow" />
        <Row gutter={[24, 24]}>
          <Col span={12}>
            <IntegrationsSection system={system} />
          </Col>
          <Col span={12}>
            <ProducerConsumerCard relationships={system.relationships} />
          </Col>
        </Row>
      </div>
      <div>
        <SectionHeader title="Datasets" />
        <DatasetsSection system={system} />
      </div>
    </Flex>
  );

  return (
    <Tabs
      items={[
        { key: "overview", label: "Overview", children: overviewContent },
        { key: "history", label: "History", children: <HistoryContent system={system} /> },
        { key: "assets", label: "Assets", children: <AssetsContent system={system} /> },
        { key: "advanced", label: "Advanced", children: <AdvancedContent system={system} /> },
      ]}
      defaultActiveKey="overview"
    />
  );
};

export default SystemDetailContent;
