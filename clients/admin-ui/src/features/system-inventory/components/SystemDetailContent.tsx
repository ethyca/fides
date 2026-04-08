import { Edit } from "@carbon/icons-react";
import {
  Avatar,
  Button,
  Card,
  Col,
  Divider,
  Flex,
  Input,
  Modal,
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

import AssetsTab from "../detail/tabs/AssetsTab";
import DatasetsTab from "../detail/tabs/DatasetsTab";
import type { MockSystem } from "../types";

interface SystemDetailContentProps {
  system: MockSystem;
}

const SectionHeader = ({ title }: { title: string }) => (
  <>
    <Title level={4} className="!my-0">
      {title}
    </Title>
    <Divider className="!mb-4 !mt-2" />
  </>
);

// --- About: symmetric two-column grid ---

const AboutField = ({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) => (
  <div className="min-h-[42px]">
    <Text
      type="secondary"
      className="mb-1 block text-[10px] uppercase tracking-wider"
    >
      {label}
    </Text>
    <Text strong className="block text-sm">
      {children}
    </Text>
  </div>
);

const AboutSection = ({ system }: { system: MockSystem }) => {
  const [editing, setEditing] = useState(false);

  return (
    <div>
      <Flex justify="space-between" align="center">
        <Title level={4} className="!my-0">
          About
        </Title>
        <Button
          type="text"
          size="small"
          icon={<Edit size={14} />}
          onClick={() => setEditing(true)}
        >
          Edit
        </Button>
      </Flex>
      <Divider className="!mb-4 !mt-2" />

      <Row gutter={[32, 16]}>
        <Col span={12}>
          <AboutField label="Type">{system.system_type}</AboutField>
        </Col>
        <Col span={12}>
          <AboutField label="Responsibility">
            {system.responsibility}
          </AboutField>
        </Col>
        <Col span={12}>
          <AboutField label="Department">{system.department}</AboutField>
        </Col>
        <Col span={12}>
          <AboutField label="Roles">
            {system.roles.length > 0
              ? system.roles
                  .map((r) => r.charAt(0).toUpperCase() + r.slice(1))
                  .join(", ")
              : "—"}
          </AboutField>
        </Col>
        <Col span={12}>
          <AboutField label="Group">{system.group ?? "—"}</AboutField>
        </Col>
        <Col span={12}>
          <AboutField label="Description">{system.description}</AboutField>
        </Col>
      </Row>

      <Modal
        title="Edit system details"
        open={editing}
        onCancel={() => setEditing(false)}
        onOk={() => setEditing(false)}
        okText="Save"
        width={600}
      >
        <Flex vertical gap={16} className="mt-4">
          <div>
            <Text type="secondary" className="mb-1 block text-xs">
              System type
            </Text>
            <Input defaultValue={system.system_type} />
          </div>
          <div>
            <Text type="secondary" className="mb-1 block text-xs">
              Department
            </Text>
            <Input defaultValue={system.department} />
          </div>
          <div>
            <Text type="secondary" className="mb-1 block text-xs">
              Responsibility
            </Text>
            <Select
              aria-label="Responsibility"
              defaultValue={system.responsibility}
              className="w-full"
              options={[
                { label: "Controller", value: "Controller" },
                { label: "Processor", value: "Processor" },
                { label: "Sub-Processor", value: "Sub-Processor" },
              ]}
            />
          </div>
          <div>
            <Text type="secondary" className="mb-1 block text-xs">
              Group
            </Text>
            <Input defaultValue={system.group ?? ""} />
          </div>
          <div>
            <Text type="secondary" className="mb-1 block text-xs">
              Roles
            </Text>
            <Select
              aria-label="Roles"
              mode="multiple"
              defaultValue={system.roles}
              className="w-full"
              options={[
                { label: "Producer", value: "producer" },
                { label: "Consumer", value: "consumer" },
              ]}
            />
          </div>
          <div>
            <Text type="secondary" className="mb-1 block text-xs">
              Description
            </Text>
            <Input.TextArea rows={3} defaultValue={system.description} />
          </div>
        </Flex>
      </Modal>
    </div>
  );
};

// --- Purpose picker modal ---

const AVAILABLE_PURPOSES = [
  {
    name: "Analytics",
    dataUse: "analytics",
    description: "Product analytics and usage tracking",
  },
  {
    name: "Advertising",
    dataUse: "advertising",
    description: "Targeted advertising and ad measurement",
  },
  {
    name: "Customer support",
    dataUse: "customer_support",
    description: "Customer service and issue resolution",
  },
  {
    name: "Fraud prevention",
    dataUse: "fraud_detection",
    description: "Fraud detection and risk scoring",
  },
  {
    name: "Marketing",
    dataUse: "marketing",
    description: "Email marketing and campaign management",
  },
  {
    name: "Finance",
    dataUse: "finance",
    description: "Billing, invoicing, and financial reporting",
  },
  {
    name: "HR",
    dataUse: "human_resources",
    description: "Employee management and payroll",
  },
  {
    name: "Personalization",
    dataUse: "personalize",
    description: "Content personalization and recommendations",
  },
  {
    name: "Security",
    dataUse: "security",
    description: "System security and threat detection",
  },
  {
    name: "Legal compliance",
    dataUse: "legal",
    description: "Regulatory compliance and legal obligations",
  },
];

const PurposePickerModal = ({
  open,
  onClose,
  existing,
}: {
  open: boolean;
  onClose: () => void;
  existing: string[];
}) => {
  const [search, setSearch] = useState("");
  const [dataUseFilter, setDataUseFilter] = useState<string | null>(null);
  const [selected, setSelected] = useState<string[]>([]);

  const dataUses = [...new Set(AVAILABLE_PURPOSES.map((p) => p.dataUse))];
  const filtered = AVAILABLE_PURPOSES.filter((p) => {
    if (existing.includes(p.name)) {
      return false;
    }
    if (
      search &&
      !p.name.toLowerCase().includes(search.toLowerCase()) &&
      !p.description.toLowerCase().includes(search.toLowerCase())
    ) {
      return false;
    }
    if (dataUseFilter && p.dataUse !== dataUseFilter) {
      return false;
    }
    return true;
  });

  return (
    <Modal
      title="Add purposes"
      open={open}
      onCancel={() => {
        setSelected([]);
        setSearch("");
        onClose();
      }}
      onOk={() => {
        setSelected([]);
        setSearch("");
        onClose();
      }}
      okText={`Add ${selected.length || ""} purpose${selected.length !== 1 ? "s" : ""}`}
      okButtonProps={{ disabled: selected.length === 0 }}
      width={560}
    >
      <Flex vertical gap={12} className="mt-3">
        <Flex gap={8}>
          <Input
            placeholder="Search purposes..."
            value={search}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setSearch(e.target.value)
            }
            allowClear
            size="small"
            className="flex-1"
          />
          <Select
            aria-label="Filter by data use"
            placeholder="All data uses"
            value={dataUseFilter}
            onChange={setDataUseFilter}
            allowClear
            size="small"
            className="w-[160px]"
            options={dataUses.map((d) => ({
              label: d.replace("_", " "),
              value: d,
            }))}
          />
        </Flex>
        <div className="max-h-[350px] overflow-y-auto">
          <Flex
            className="border-b border-solid border-[#f0f0f0] px-3 py-1.5"
            style={{ backgroundColor: palette.FIDESUI_NEUTRAL_75 }}
          >
            <Text
              strong
              className="w-[30%] text-[10px] uppercase tracking-wider"
            >
              Purpose
            </Text>
            <Text strong className="w-1/4 text-[10px] uppercase tracking-wider">
              Data Use
            </Text>
            <Text
              strong
              className="w-[45%] text-[10px] uppercase tracking-wider"
            >
              Description
            </Text>
          </Flex>
          {filtered.map((p) => {
            const isSelected = selected.includes(p.name);
            return (
              <Flex
                key={p.name}
                align="center"
                className="cursor-pointer border-b border-solid border-[#f5f5f5] px-3 py-2 hover:bg-[#fafafa]"
                onClick={() =>
                  setSelected(
                    isSelected
                      ? selected.filter((n) => n !== p.name)
                      : [...selected, p.name],
                  )
                }
              >
                <Text strong={isSelected} className="w-[30%] text-xs">
                  {p.name}
                </Text>
                <Text type="secondary" className="w-1/4 text-xs">
                  {p.dataUse.replace("_", " ")}
                </Text>
                <Flex
                  className="w-[45%]"
                  justify="space-between"
                  align="center"
                >
                  <Text type="secondary" className="text-xs">
                    {p.description}
                  </Text>
                  {isSelected && (
                    <Tag
                      color="success"
                      bordered={false}
                      className="!ml-2 !text-[10px]"
                    >
                      Selected
                    </Tag>
                  )}
                </Flex>
              </Flex>
            );
          })}
          {filtered.length === 0 && (
            <Flex justify="center" className="py-6">
              <Text type="secondary" className="text-xs">
                No purposes available
              </Text>
            </Flex>
          )}
        </div>
      </Flex>
    </Modal>
  );
};

// --- Steward picker modal ---

const AVAILABLE_STEWARDS = [
  {
    name: "Jack Gale",
    email: "jack.gale@ethyca.com",
    role: "Engineering Lead",
    initials: "JG",
  },
  {
    name: "Anna Kim",
    email: "anna.kim@ethyca.com",
    role: "Privacy Engineer",
    initials: "AK",
  },
  {
    name: "Rachel Smith",
    email: "rachel.smith@ethyca.com",
    role: "Data Governance Manager",
    initials: "RS",
  },
  {
    name: "Mike Brown",
    email: "mike.brown@ethyca.com",
    role: "Finance Director",
    initials: "MB",
  },
  {
    name: "Lisa Torres",
    email: "lisa.torres@ethyca.com",
    role: "Sales Operations",
    initials: "LT",
  },
  {
    name: "Chris Kelly",
    email: "chris.kelly@ethyca.com",
    role: "Trust & Safety Lead",
    initials: "CK",
  },
  {
    name: "Diana Park",
    email: "diana.park@ethyca.com",
    role: "HR Director",
    initials: "DP",
  },
  {
    name: "Sam Chen",
    email: "sam.chen@ethyca.com",
    role: "Security Engineer",
    initials: "SC",
  },
];

const StewardPickerModal = ({
  open,
  onClose,
  existing,
}: {
  open: boolean;
  onClose: () => void;
  existing: string[];
}) => {
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<string[]>([]);

  const filtered = AVAILABLE_STEWARDS.filter((s) => {
    if (existing.includes(s.initials)) {
      return false;
    }
    if (search) {
      const q = search.toLowerCase();
      if (
        !s.name.toLowerCase().includes(q) &&
        !s.email.toLowerCase().includes(q) &&
        !s.role.toLowerCase().includes(q)
      ) {
        return false;
      }
    }
    return true;
  });

  return (
    <Modal
      title="Add stewards"
      open={open}
      onCancel={() => {
        setSelected([]);
        setSearch("");
        onClose();
      }}
      onOk={() => {
        setSelected([]);
        setSearch("");
        onClose();
      }}
      okText={`Add ${selected.length || ""} steward${selected.length !== 1 ? "s" : ""}`}
      okButtonProps={{ disabled: selected.length === 0 }}
      width={560}
    >
      <Flex vertical gap={12} className="mt-3">
        <Input
          placeholder="Search by name, email, or role..."
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setSearch(e.target.value)
          }
          allowClear
          size="small"
        />
        <div className="max-h-[350px] overflow-y-auto">
          <Flex
            className="border-b border-solid border-[#f0f0f0] px-3 py-1.5"
            style={{ backgroundColor: palette.FIDESUI_NEUTRAL_75 }}
          >
            <Text
              strong
              className="w-[30%] text-[10px] uppercase tracking-wider"
            >
              Name
            </Text>
            <Text
              strong
              className="w-[35%] text-[10px] uppercase tracking-wider"
            >
              Email
            </Text>
            <Text
              strong
              className="w-[35%] text-[10px] uppercase tracking-wider"
            >
              Role
            </Text>
          </Flex>
          {filtered.map((s) => {
            const isSelected = selected.includes(s.initials);
            return (
              <Flex
                key={s.initials}
                align="center"
                className="cursor-pointer border-b border-solid border-[#f5f5f5] px-3 py-2 hover:bg-[#fafafa]"
                onClick={() =>
                  setSelected(
                    isSelected
                      ? selected.filter((i) => i !== s.initials)
                      : [...selected, s.initials],
                  )
                }
              >
                <Flex align="center" gap={8} className="w-[30%]">
                  <Avatar
                    size={22}
                    style={{
                      backgroundColor: "#e6e6e8",
                      color: "#53575c",
                      fontSize: 9,
                    }}
                  >
                    {s.initials}
                  </Avatar>
                  <Text strong={isSelected} className="text-xs">
                    {s.name}
                  </Text>
                </Flex>
                <Text type="secondary" className="w-[35%] text-xs">
                  {s.email}
                </Text>
                <Flex
                  className="w-[35%]"
                  justify="space-between"
                  align="center"
                >
                  <Text type="secondary" className="text-xs">
                    {s.role}
                  </Text>
                  {isSelected && (
                    <Tag
                      color="success"
                      bordered={false}
                      className="!text-[10px]"
                    >
                      Selected
                    </Tag>
                  )}
                </Flex>
              </Flex>
            );
          })}
          {filtered.length === 0 && (
            <Flex justify="center" className="py-6">
              <Text type="secondary" className="text-xs">
                No stewards available
              </Text>
            </Flex>
          )}
        </div>
      </Flex>
    </Modal>
  );
};

// --- Governance cards ---

const PurposesSection = ({ system }: { system: MockSystem }) => {
  const [pickerOpen, setPickerOpen] = useState(false);
  return (
    <Card
      size="small"
      className="h-full"
      title={
        <Text strong className="text-sm">
          Purposes
        </Text>
      }
      extra={
        <Button type="text" size="small" onClick={() => setPickerOpen(true)}>
          + Add
        </Button>
      }
    >
      {system.purposes.length > 0 ? (
        <Flex gap={6} wrap>
          {system.purposes.map((p) => (
            <Tag
              key={p.name}
              bordered={false}
              style={{ backgroundColor: palette.FIDESUI_NEUTRAL_100 }}
            >
              {p.name}
            </Tag>
          ))}
        </Flex>
      ) : (
        <Text type="secondary" className="text-xs">
          No purposes defined
        </Text>
      )}
      <PurposePickerModal
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        existing={system.purposes.map((p) => p.name)}
      />
    </Card>
  );
};

const StewardsSection = ({ system }: { system: MockSystem }) => {
  const [pickerOpen, setPickerOpen] = useState(false);
  return (
    <Card
      size="small"
      className="h-full"
      title={
        <Text strong className="text-sm">
          Stewards
        </Text>
      }
      extra={
        <Button type="text" size="small" onClick={() => setPickerOpen(true)}>
          + Add
        </Button>
      }
    >
      {system.stewards.length > 0 ? (
        <Flex vertical gap={8}>
          {system.stewards.map((st) => (
            <Flex key={st.initials} align="center" gap={8}>
              <Avatar
                size={24}
                style={{
                  backgroundColor: "#e6e6e8",
                  color: "#53575c",
                  fontSize: 10,
                }}
              >
                {st.initials}
              </Avatar>
              <Text className="text-xs">{st.name}</Text>
            </Flex>
          ))}
        </Flex>
      ) : (
        <Text type="secondary" className="text-xs">
          No steward assigned
        </Text>
      )}
      <StewardPickerModal
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        existing={system.stewards.map((s) => s.initials)}
      />
    </Card>
  );
};

// --- Classification (compact with mini metric cards) ---

const getMonitorStatusColor = (
  status: string,
): "success" | "error" | "warning" => {
  if (status === "completed") {
    return "success";
  }
  if (status === "failed") {
    return "error";
  }
  return "warning";
};

const getIntegrationStatusColor = (
  status: string,
): "success" | "error" | "warning" | "default" => {
  if (status === "active") {
    return "success";
  }
  if (status === "failed") {
    return "error";
  }
  if (status === "untested") {
    return "warning";
  }
  return "default";
};

const ClassificationSection = ({ system }: { system: MockSystem }) => {
  const { approved, pending, unreviewed, categories } = system.classification;
  const total = approved + pending + unreviewed;

  return (
    <Card
      size="small"
      title={
        <Text strong className="text-sm">
          Classification Progress
        </Text>
      }
      extra={
        <Text
          className="cursor-pointer text-xs"
          style={{ color: palette.FIDESUI_MINOS }}
        >
          Review fields &rarr;
        </Text>
      }
    >
      <Row gutter={24}>
        {/* Col 1: Progress bar */}
        <Col span={8}>
          {total > 0 && (
            <Flex vertical gap={8}>
              <Flex className="h-[10px] w-full overflow-hidden rounded-full">
                <div
                  style={{
                    width: `${(approved / total) * 100}%`,
                    backgroundColor: "#5a9a68",
                  }}
                />
                <div
                  style={{
                    width: `${(pending / total) * 100}%`,
                    backgroundColor: "#4a90e2",
                  }}
                />
                <div
                  style={{
                    width: `${(unreviewed / total) * 100}%`,
                    backgroundColor: "#e6e6e8",
                  }}
                />
              </Flex>
              <Flex vertical gap={3}>
                <Flex align="center" gap={4}>
                  <div
                    className="size-[6px] rounded-full"
                    style={{ backgroundColor: "#5a9a68" }}
                  />
                  <Text className="text-[10px]">{approved} approved</Text>
                </Flex>
                <Flex align="center" gap={4}>
                  <div
                    className="size-[6px] rounded-full"
                    style={{ backgroundColor: "#4a90e2" }}
                  />
                  <Text className="text-[10px]">{pending} classified</Text>
                </Flex>
                <Flex align="center" gap={4}>
                  <div
                    className="size-[6px] rounded-full"
                    style={{ backgroundColor: "#e6e6e8" }}
                  />
                  <Text className="text-[10px]">{unreviewed} unlabeled</Text>
                </Flex>
              </Flex>
            </Flex>
          )}
        </Col>

        {/* Col 2: Monitors */}
        <Col span={8} className="border-l border-solid border-[#f0f0f0] pl-6">
          <Text
            strong
            className="mb-2 block text-[10px] uppercase tracking-wider"
          >
            Monitors
          </Text>
          {system.monitors.length > 0 ? (
            <Flex vertical gap={4}>
              {system.monitors.map((mon) => (
                <Flex key={mon.name} justify="space-between" align="center">
                  <Text className="text-xs">{mon.name}</Text>
                  <Flex align="center" gap={6}>
                    <Text type="secondary" className="text-[10px]">
                      {mon.resourceCount}
                    </Text>
                    <Tag
                      color={getMonitorStatusColor(mon.status)}
                      bordered={false}
                      className="!text-[9px]"
                    >
                      {mon.status}
                    </Tag>
                  </Flex>
                </Flex>
              ))}
            </Flex>
          ) : (
            <Text type="secondary" className="text-xs">
              No monitors
            </Text>
          )}
        </Col>

        {/* Col 3: Categories */}
        <Col span={8} className="border-l border-solid border-[#f0f0f0] pl-6">
          <Text
            strong
            className="mb-2 block text-[10px] uppercase tracking-wider"
          >
            Categories
          </Text>
          {categories.length > 0 ? (
            <Flex vertical gap={4}>
              {categories.map((cat) => (
                <Flex key={cat.name} justify="space-between" align="center">
                  <Text className="text-xs">{cat.name}</Text>
                  <Flex align="center" gap={6}>
                    <Text type="secondary" className="text-[10px]">
                      {cat.fieldCount} fields
                    </Text>
                    <Text strong className="text-xs">
                      {cat.approvedPercent}%
                    </Text>
                  </Flex>
                </Flex>
              ))}
            </Flex>
          ) : (
            <Text type="secondary" className="text-xs">
              No categories
            </Text>
          )}
        </Col>
      </Row>
    </Card>
  );
};

// --- Integrations (with Scopes header + button actions) ---

// --- Integration picker modal ---

const AVAILABLE_INTEGRATIONS = [
  {
    name: "Snowflake Connector",
    type: "Snowflake",
    capabilities: ["access", "erasure"],
  },
  {
    name: "PostgreSQL",
    type: "PostgreSQL",
    capabilities: ["access", "erasure"],
  },
  { name: "MongoDB", type: "MongoDB", capabilities: ["access", "erasure"] },
  { name: "S3 Bucket", type: "AWS S3", capabilities: ["access"] },
  { name: "Redshift", type: "Redshift", capabilities: ["access", "erasure"] },
  { name: "MySQL", type: "MySQL", capabilities: ["access", "erasure"] },
  { name: "DynamoDB", type: "DynamoDB", capabilities: ["access"] },
  { name: "Stripe API", type: "Stripe", capabilities: ["access", "erasure"] },
  {
    name: "Salesforce API",
    type: "Salesforce",
    capabilities: ["access", "erasure"],
  },
  { name: "HubSpot API", type: "HubSpot", capabilities: ["access"] },
];

const IntegrationPickerModal = ({
  open,
  onClose,
  existing,
}: {
  open: boolean;
  onClose: () => void;
  existing: string[];
}) => {
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<string[]>([]);

  const filtered = AVAILABLE_INTEGRATIONS.filter((intg) => {
    if (existing.includes(intg.name)) {
      return false;
    }
    if (
      search &&
      !intg.name.toLowerCase().includes(search.toLowerCase()) &&
      !intg.type.toLowerCase().includes(search.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  return (
    <Modal
      title="Add integration"
      open={open}
      onCancel={() => {
        setSelected([]);
        setSearch("");
        onClose();
      }}
      onOk={() => {
        setSelected([]);
        setSearch("");
        onClose();
      }}
      okText={`Add ${selected.length || ""} integration${selected.length !== 1 ? "s" : ""}`}
      okButtonProps={{ disabled: selected.length === 0 }}
      width={560}
    >
      <Flex vertical gap={12} className="mt-3">
        <Input
          placeholder="Search integrations..."
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setSearch(e.target.value)
          }
          allowClear
          size="small"
        />
        <div className="max-h-[350px] overflow-y-auto">
          <Flex
            className="border-b border-solid border-[#f0f0f0] px-3 py-1.5"
            style={{ backgroundColor: palette.FIDESUI_NEUTRAL_75 }}
          >
            <Text
              strong
              className="w-[35%] text-[10px] uppercase tracking-wider"
            >
              Name
            </Text>
            <Text strong className="w-1/4 text-[10px] uppercase tracking-wider">
              Type
            </Text>
            <Text strong className="w-2/5 text-[10px] uppercase tracking-wider">
              Capabilities
            </Text>
          </Flex>
          {filtered.map((intg) => {
            const isSelected = selected.includes(intg.name);
            return (
              <Flex
                key={intg.name}
                align="center"
                className="cursor-pointer border-b border-solid border-[#f5f5f5] px-3 py-2 hover:bg-[#fafafa]"
                onClick={() =>
                  setSelected(
                    isSelected
                      ? selected.filter((n) => n !== intg.name)
                      : [...selected, intg.name],
                  )
                }
              >
                <Text strong={isSelected} className="w-[35%] text-xs">
                  {intg.name}
                </Text>
                <Text type="secondary" className="w-1/4 text-xs">
                  {intg.type}
                </Text>
                <Flex className="w-2/5" justify="space-between" align="center">
                  <Flex gap={4}>
                    {intg.capabilities.map((c) => (
                      <Tag
                        key={c}
                        bordered={false}
                        color="olive"
                        className="!text-[9px]"
                      >
                        {c}
                      </Tag>
                    ))}
                  </Flex>
                  {isSelected && (
                    <Tag
                      color="success"
                      bordered={false}
                      className="!text-[10px]"
                    >
                      Selected
                    </Tag>
                  )}
                </Flex>
              </Flex>
            );
          })}
          {filtered.length === 0 && (
            <Flex justify="center" className="py-6">
              <Text type="secondary" className="text-xs">
                No integrations available
              </Text>
            </Flex>
          )}
        </div>
      </Flex>
    </Modal>
  );
};

// --- Integration edit modal ---

const IntegrationEditModal = ({
  open,
  onClose,
  integration,
}: {
  open: boolean;
  onClose: () => void;
  integration: MockSystem["integrations"][0] | null;
}) => (
  <Modal
    title={integration ? `Edit ${integration.name}` : "Edit integration"}
    open={open}
    onCancel={onClose}
    onOk={onClose}
    okText="Save"
    width={600}
  >
    {integration && (
      <Flex vertical gap={16} className="mt-4">
        <Flex gap={16}>
          <div className="flex-1">
            <Text type="secondary" className="mb-1 block text-xs">
              Name
            </Text>
            <Input defaultValue={integration.name} disabled />
          </div>
          <div className="flex-1">
            <Text type="secondary" className="mb-1 block text-xs">
              Type
            </Text>
            <Input defaultValue={integration.type} disabled />
          </div>
        </Flex>
        <Flex gap={16}>
          <div className="flex-1">
            <Text type="secondary" className="mb-1 block text-xs">
              Access level
            </Text>
            <Select
              aria-label="Access level"
              defaultValue={integration.accessLevel}
              className="w-full"
              options={[
                { label: "Read", value: "Read" },
                { label: "Read/Write", value: "Read/Write" },
                { label: "Write", value: "Write" },
              ]}
            />
          </div>
          <div className="flex-1">
            <Text type="secondary" className="mb-1 block text-xs">
              Capabilities
            </Text>
            <Select
              aria-label="Capabilities"
              mode="multiple"
              defaultValue={integration.enabledActions}
              className="w-full"
              options={[
                { label: "DSR access", value: "DSR access" },
                { label: "DSR erasure", value: "DSR erasure" },
                { label: "Monitoring", value: "monitoring" },
                { label: "Classification", value: "classification" },
                { label: "Consent", value: "consent" },
              ]}
            />
          </div>
        </Flex>
        <Divider className="!my-0" />
        <Text strong className="text-xs">
          Credentials
        </Text>
        <div>
          <Text type="secondary" className="mb-1 block text-xs">
            Keyfile credentials
          </Text>
          <Text type="secondary" className="mb-2 block text-[10px]">
            The contents of the key file that contains authentication
            credentials for a service account in GCP.
          </Text>
          <Input.TextArea
            rows={6}
            className="!font-mono !text-xs"
            defaultValue={JSON.stringify(
              {
                type: "service_account",
                project_id: "ethyca-production",
                private_key_id: "••••••••",
                private_key: "••••••••",
                client_email:
                  "fides-sa@ethyca-production.iam.gserviceaccount.com",
                client_id: "1234567890",
                auth_uri: "https://accounts.google.com/o/oauth2/auth",
                token_uri: "https://oauth2.googleapis.com/token",
              },
              null,
              2,
            )}
          />
        </div>
        <Flex gap={16}>
          <div className="flex-1">
            <Text type="secondary" className="mb-1 block text-xs">
              Project ID
            </Text>
            <Input defaultValue="ethyca-production" />
          </div>
          <div className="flex-1">
            <Text type="secondary" className="mb-1 block text-xs">
              Dataset
            </Text>
            <Text type="secondary" className="mb-1 block text-[10px]">
              Leave blank to include all datasets.
            </Text>
            <Input placeholder="Optional — scope to specific dataset" />
          </div>
        </Flex>
      </Flex>
    )}
  </Modal>
);

// --- Integrations section ---

const IntegrationsSection = ({ system }: { system: MockSystem }) => {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [editIntg, setEditIntg] = useState<
    MockSystem["integrations"][0] | null
  >(null);
  const [deleteIntg, setDeleteIntg] = useState<string | null>(null);

  return (
    <div>
      <SectionHeader title="Integrations" />
      <Flex justify="space-between" align="flex-start" className="mb-3">
        <Text type="secondary" className="max-w-[75%] text-xs">
          Integrations connect Fides to this system for automated privacy
          operations — executing DSR access and erasure requests, monitoring
          schema changes, scanning for sensitive data, and enforcing consent
          preferences.
        </Text>
        <Button type="primary" size="small" onClick={() => setPickerOpen(true)}>
          + Add integration
        </Button>
      </Flex>
      {system.integrations.length > 0 ? (
        <Flex vertical gap={0}>
          <Flex
            className="border-b border-solid border-[#f0f0f0] px-3 py-2"
            style={{ backgroundColor: palette.FIDESUI_CORINTH }}
          >
            <Text
              strong
              className="w-[26%] text-[10px] uppercase tracking-wider"
            >
              Name
            </Text>
            <Text
              strong
              className="w-[12%] text-[10px] uppercase tracking-wider"
            >
              Type
            </Text>
            <Text
              strong
              className="w-[10%] text-[10px] uppercase tracking-wider"
            >
              Status
            </Text>
            <Text
              strong
              className="w-[14%] text-[10px] uppercase tracking-wider"
            >
              Last tested
            </Text>
            <Text
              strong
              className="w-[14%] text-[10px] uppercase tracking-wider"
            >
              Capabilities
            </Text>
            <Text
              strong
              className="w-[24%] text-right text-[10px] uppercase tracking-wider"
            >
              Actions
            </Text>
          </Flex>
          {system.integrations.map((intg) => (
            <Flex
              key={intg.name}
              align="center"
              className="border-b border-solid border-[#f5f5f5] px-3 py-2.5"
            >
              <Text className="w-[26%] text-xs">{intg.name}</Text>
              <Text type="secondary" className="w-[12%] text-xs">
                {intg.type}
              </Text>
              <div className="w-[10%]">
                <Tag
                  color={getIntegrationStatusColor(intg.status)}
                  bordered={false}
                  className="!text-[10px]"
                >
                  {intg.status}
                </Tag>
              </div>
              <Text type="secondary" className="w-[14%] text-xs">
                {intg.lastTested
                  ? new Date(intg.lastTested).toLocaleDateString()
                  : "—"}
              </Text>
              <Text type="secondary" className="w-[14%] text-xs">
                {intg.enabledActions.join(", ")}
              </Text>
              <Flex className="w-[24%]" justify="flex-end" gap={6}>
                <Button
                  size="small"
                  type="default"
                  className="!text-[11px]"
                  onClick={() => setEditIntg(intg)}
                >
                  Edit
                </Button>
                <Button size="small" type="default" className="!text-[11px]">
                  Test
                </Button>
                <Button
                  size="small"
                  type="text"
                  danger
                  className="!text-[11px]"
                  onClick={() => setDeleteIntg(intg.name)}
                >
                  Remove
                </Button>
              </Flex>
            </Flex>
          ))}
        </Flex>
      ) : (
        <Text type="secondary" className="text-xs">
          No integrations configured
        </Text>
      )}
      <IntegrationPickerModal
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        existing={system.integrations.map((i) => i.name)}
      />
      <IntegrationEditModal
        open={!!editIntg}
        onClose={() => setEditIntg(null)}
        integration={editIntg}
      />
      <Modal
        title="Remove integration"
        open={!!deleteIntg}
        onCancel={() => setDeleteIntg(null)}
        onOk={() => setDeleteIntg(null)}
        okText="Remove"
        okButtonProps={{ danger: true }}
        width={420}
      >
        <Text>
          Are you sure you want to remove <Text strong>{deleteIntg}</Text>? This
          will disconnect the integration from this system.
        </Text>
      </Modal>
    </div>
  );
};

// --- Activity (with colored status dots) ---

// --- History Tab (GRC audit log) ---

const CATEGORY_TAG_COLORS: Record<
  string,
  "sandstone" | "nectar" | "olive" | "minos" | "default"
> = {
  classification: "sandstone",
  steward: "nectar",
  integration: "olive",
  purpose: "minos",
  system: "default",
};

const HistoryChangeCell = ({
  oldValue,
  newValue,
}: {
  oldValue?: string;
  newValue?: string;
}) => {
  if (oldValue) {
    return (
      <Text className="text-[10px]">
        <Text type="secondary" className="text-[10px]" delete>
          {oldValue}
        </Text>
        {" → "}
        <Text strong className="text-[10px]">
          {newValue}
        </Text>
      </Text>
    );
  }
  if (newValue) {
    return (
      <Text strong className="text-[10px]">
        {newValue}
      </Text>
    );
  }
  return (
    <Text type="secondary" className="text-[10px]">
      —
    </Text>
  );
};

const HistoryContent = ({ system }: { system: MockSystem }) => {
  const [categoryFilter, setCategoryFilter] = useState<string[]>([]);
  const [userFilter, setUserFilter] = useState<string[]>([]);
  const [search, setSearch] = useState("");

  const categories = [...new Set(system.history.map((e) => e.category))].sort();
  const users = [...new Set(system.history.map((e) => e.user))].sort();

  const filtered = system.history.filter((entry) => {
    if (categoryFilter.length > 0 && !categoryFilter.includes(entry.category)) {
      return false;
    }
    if (userFilter.length > 0 && !userFilter.includes(entry.user)) {
      return false;
    }
    if (search) {
      const q = search.toLowerCase();
      if (
        !entry.action.toLowerCase().includes(q) &&
        !entry.detail.toLowerCase().includes(q) &&
        !entry.fieldName?.toLowerCase().includes(q)
      ) {
        return false;
      }
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
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setSearch(e.target.value)
          }
          allowClear
          size="small"
          style={{ width: 260 }}
        />
        <Flex gap={12} align="center">
          <Select
            aria-label="Filter by category"
            mode="multiple"
            placeholder="All categories"
            value={categoryFilter}
            onChange={setCategoryFilter}
            allowClear
            className="w-[180px]"
            size="small"
            options={categories.map((c) => ({
              label: c.charAt(0).toUpperCase() + c.slice(1),
              value: c,
            }))}
          />
          <Select
            aria-label="Filter by user"
            mode="multiple"
            placeholder="All users"
            value={userFilter}
            onChange={setUserFilter}
            allowClear
            className="w-[180px]"
            size="small"
            options={users.map((u) => ({ label: u, value: u }))}
          />
          <Text type="secondary" className="text-xs">
            {filtered.length} entries
          </Text>
        </Flex>
      </Flex>

      {/* Table */}
      <div className="max-h-[700px] overflow-y-auto">
        {/* Header */}
        <Flex
          className="sticky top-0 z-10 border-b border-solid border-[#f0f0f0] px-3 py-2"
          style={{ backgroundColor: palette.FIDESUI_CORINTH }}
        >
          <Text strong className="w-[12%] text-[10px] uppercase tracking-wider">
            Date
          </Text>
          <Text strong className="w-[10%] text-[10px] uppercase tracking-wider">
            Category
          </Text>
          <Text strong className="w-[14%] text-[10px] uppercase tracking-wider">
            Action
          </Text>
          <Text strong className="w-[10%] text-[10px] uppercase tracking-wider">
            User
          </Text>
          <Text strong className="w-[12%] text-[10px] uppercase tracking-wider">
            Field
          </Text>
          <Text strong className="w-[18%] text-[10px] uppercase tracking-wider">
            Change
          </Text>
          <Text strong className="w-[24%] text-[10px] uppercase tracking-wider">
            Reason
          </Text>
        </Flex>

        {/* Rows */}
        {filtered.map((entry) => (
          <Flex
            key={`${entry.timestamp}-${entry.action}-${entry.category}`}
            align="center"
            className="border-b border-solid border-[#f5f5f5] px-3 py-2"
          >
            <Text type="secondary" className="w-[12%] text-[10px]">
              {new Date(entry.timestamp).toLocaleString(undefined, {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </Text>
            <div className="w-[10%]">
              <Tag
                color={CATEGORY_TAG_COLORS[entry.category] ?? "default"}
                bordered={false}
                className="!text-[9px]"
              >
                {entry.category}
              </Tag>
            </div>
            <Text className="w-[14%] text-xs">{entry.action}</Text>
            <Flex align="center" gap={4} className="w-[10%]">
              <Avatar
                size={18}
                style={{
                  backgroundColor: "#e6e6e8",
                  color: "#53575c",
                  fontSize: 8,
                }}
              >
                {entry.user.slice(0, 2).toUpperCase()}
              </Avatar>
              <Text className="text-[10px]">{entry.user.split(" ")[0]}</Text>
            </Flex>
            <Text
              type="secondary"
              className="w-[12%] truncate text-[10px]"
              title={entry.fieldName}
            >
              {entry.fieldName ?? "—"}
            </Text>
            <div className="w-[18%]">
              <HistoryChangeCell
                oldValue={entry.oldValue}
                newValue={entry.newValue}
              />
            </div>
            <Text
              type="secondary"
              className="w-[24%] truncate text-[10px]"
              title={entry.reason}
            >
              {entry.reason ?? "—"}
            </Text>
          </Flex>
        ))}

        {filtered.length === 0 && (
          <Flex justify="center" className="py-8">
            <Text type="secondary" className="text-xs">
              No entries match the current filters
            </Text>
          </Flex>
        )}
      </div>
    </Flex>
  );
};

// --- Advanced Tab (flat left-right form) ---

// --- Advanced Tab ---

const FormField = ({
  label,
  children,
  span = 1,
}: {
  label: string;
  children: React.ReactNode;
  span?: 1 | 2;
}) => (
  <div className={span === 2 ? "col-span-2" : ""}>
    <Text type="secondary" className="mb-1 block text-xs">
      {label}
    </Text>
    {children}
  </div>
);

const FormGroup = ({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) => (
  <div className="rounded-lg border border-solid border-[#f0f0f0]">
    <div
      className="rounded-t-lg px-5 py-3"
      style={{ backgroundColor: palette.FIDESUI_NEUTRAL_75 }}
    >
      <Text strong className="text-sm">
        {title}
      </Text>
    </div>
    <div className="grid grid-cols-2 gap-x-6 gap-y-4 px-5 py-4">{children}</div>
  </div>
);

const AdvancedContent = () => (
  <Flex vertical gap={20} className="max-w-[900px]">
    <FormGroup title="Data Processing">
      <FormField label="Processes personal data">
        <Switch aria-label="Processes personal data" defaultChecked />
      </FormField>
      <FormField label="Exempt from privacy regulations">
        <Switch aria-label="Exempt from privacy regulations" />
      </FormField>
      <FormField label="Reason for exemption" span={2}>
        <Input placeholder="Enter reason..." />
      </FormField>
      <FormField label="Uses profiling">
        <Switch aria-label="Uses profiling" />
      </FormField>
      <FormField label="Requires data protection assessments">
        <Switch aria-label="Requires data protection assessments" />
      </FormField>
      <FormField label="Legal basis for profiling" span={2}>
        <Select
          aria-label="Legal basis for profiling"
          mode="multiple"
          className="w-full"
          placeholder="Select..."
          options={[
            { label: "Consent", value: "consent" },
            { label: "Contract", value: "contract" },
            { label: "Legal obligation", value: "legal_obligation" },
            { label: "Vital interests", value: "vital_interests" },
            { label: "Public interest", value: "public_interest" },
            { label: "Legitimate interests", value: "legitimate_interests" },
          ]}
        />
      </FormField>
      <FormField label="Does international transfers">
        <Switch aria-label="Does international transfers" />
      </FormField>
      <FormField label="DPIA/DPA location">
        <Input placeholder="URL or file path..." />
      </FormField>
      <FormField label="Legal basis for transfers" span={2}>
        <Select
          aria-label="Legal basis for transfers"
          mode="multiple"
          className="w-full"
          placeholder="Select..."
          options={[
            { label: "Adequacy decision", value: "adequacy" },
            { label: "SCCs", value: "sccs" },
            { label: "BCRs", value: "bcrs" },
            { label: "Derogations", value: "derogations" },
          ]}
        />
      </FormField>
    </FormGroup>

    <FormGroup title="Cookie Properties">
      <FormField label="Uses cookies">
        <Switch aria-label="Uses cookies" />
      </FormField>
      <FormField label="Refreshes cookies">
        <Switch aria-label="Refreshes cookies" />
      </FormField>
      <FormField label="Uses non-cookie trackers">
        <Switch aria-label="Uses non-cookie trackers" />
      </FormField>
      <FormField label="Cookie max age (seconds)">
        <Input type="number" placeholder="e.g. 31536000" />
      </FormField>
    </FormGroup>

    <FormGroup title="Administrative">
      <FormField label="Privacy policy URL">
        <Input placeholder="https://..." />
      </FormField>
      <FormField label="Legal name">
        <Input placeholder="Legal entity name..." />
      </FormField>
      <FormField label="Legal contact / DPO">
        <Input placeholder="Contact name or email..." />
      </FormField>
      <FormField label="Joint controller info">
        <Input placeholder="Joint controller details..." />
      </FormField>
      <FormField label="Legal address" span={2}>
        <Input.TextArea rows={2} placeholder="Full legal address..." />
      </FormField>
      <FormField label="Data security practices" span={2}>
        <Input.TextArea rows={2} placeholder="Describe security measures..." />
      </FormField>
      <FormField label="Legitimate interest disclosure URL" span={2}>
        <Input placeholder="https://..." />
      </FormField>
    </FormGroup>

    <FormGroup title="Tags & Custom Fields">
      <FormField label="System tags" span={2}>
        <Select
          aria-label="System tags"
          mode="tags"
          className="w-full"
          placeholder="Add tags..."
        />
      </FormField>
      <FormField label="Custom fields" span={2}>
        <Text type="secondary" className="text-xs">
          Custom fields will appear here once the system is saved.
        </Text>
      </FormField>
    </FormGroup>

    <Flex gap={8} justify="flex-end">
      <Button>Cancel</Button>
      <Button type="primary">Save changes</Button>
    </Flex>
  </Flex>
);

// --- Main ---

const SystemDetailContent = ({ system }: SystemDetailContentProps) => {
  const overviewContent = (
    <Flex vertical gap={40}>
      <AboutSection system={system} />
      <div>
        <SectionHeader title="Governance" />
        <Text type="secondary" className="mb-4 block text-xs">
          Purposes define the legal basis and business reason for processing
          personal data in this system. Stewards are the individuals accountable
          for maintaining governance compliance and responding to data subject
          requests.
        </Text>
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <PurposesSection system={system} />
          </Col>
          <Col span={12}>
            <StewardsSection system={system} />
          </Col>
        </Row>
      </div>
      <IntegrationsSection system={system} />
      <div>
        <SectionHeader title="Classification" />
        <Text type="secondary" className="mb-4 block text-xs">
          Classification tracks how fields across this system&apos;s datasets
          are labeled with data categories. Approved fields have been reviewed
          and confirmed, classified fields are pending steward review, and
          unlabeled fields need initial categorization. {system.monitors.length}{" "}
          monitor{system.monitors.length !== 1 ? "s" : ""} actively scanning
          this system.
        </Text>
        <ClassificationSection system={system} />
      </div>
    </Flex>
  );

  return (
    <Tabs
      items={[
        { key: "overview", label: "Overview", children: overviewContent },
        {
          key: "datasets",
          label: "Datasets",
          children: <DatasetsTab system={system} />,
        },
        {
          key: "history",
          label: "History",
          children: <HistoryContent system={system} />,
        },
        {
          key: "assets",
          label: "Assets",
          children: <AssetsTab system={system} />,
        },
        {
          key: "advanced",
          label: "Advanced",
          children: <AdvancedContent />,
        },
      ]}
      defaultActiveKey="overview"
    />
  );
};

export default SystemDetailContent;
