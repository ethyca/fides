import { Edit } from "@carbon/icons-react";
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

import { CAPABILITY_TAG_COLORS } from "../constants";
import type { MockSystem } from "../types";
import { getSystemCapabilities } from "../utils";
import DatasetsCard from "../detail/cards/DatasetsCard";
import MonitorsCard from "../detail/cards/MonitorsCard";
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
  <div>
    <Text type="secondary" className="mb-1 block text-[10px] uppercase tracking-wider">{label}</Text>
    <Text className="text-sm">{children}</Text>
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

      <Text type="secondary" className="mb-4 block text-sm leading-relaxed">{system.description}</Text>

      <Row gutter={[32, 16]}>
        <Col span={12}><AboutField label="Type">{system.system_type}</AboutField></Col>
        <Col span={12}><AboutField label="Responsibility">{system.responsibility}</AboutField></Col>
        <Col span={12}><AboutField label="Department">{system.department}</AboutField></Col>
        <Col span={12}>
          <AboutField label="Roles">
            <Flex gap={4}>
              {system.roles.length > 0 ? system.roles.map((r) => (
                <Tag key={r} bordered={false} style={{ backgroundColor: palette.FIDESUI_NEUTRAL_100 }}>{r}</Tag>
              )) : "—"}
            </Flex>
          </AboutField>
        </Col>
        <Col span={12}><AboutField label="Group">{system.group ?? "—"}</AboutField></Col>
        <Col span={12}>
          <AboutField label="Annotation">
            <Flex align="center" gap={8}>
              <Progress
                type="circle"
                percent={system.annotation_percent}
                size={24}
                strokeColor={system.annotation_percent >= 75 ? "#5a9a68" : system.annotation_percent >= 40 ? "#e59d47" : "#d9534f"}
                strokeWidth={12}
                format={(p) => <Text className="!text-[7px]">{p}</Text>}
              />
              <Text className="text-sm">{system.annotation_percent}%</Text>
            </Flex>
          </AboutField>
        </Col>
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
            {capabilities.map((cap) => (
              <Tag key={cap} color={CAPABILITY_TAG_COLORS[cap]}>{cap}</Tag>
            ))}
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
  const pct = total > 0 ? Math.round((approved / total) * 100) : 0;

  return (
    <Card size="small" title={<Text strong className="text-sm">Classification Coverage</Text>} extra={<Text className="cursor-pointer text-xs" style={{ color: palette.FIDESUI_MINOS }}>Review fields &rarr;</Text>}>
      <Row gutter={24}>
        <Col span={12}>
          <Progress percent={pct} showInfo={false} strokeColor="#5a9a68" className="!mb-3 [&_.ant-progress-inner]:!h-[8px] [&_.ant-progress-inner]:!rounded-full" />
          <Flex gap={8}>
            <MiniMetric label="Approved" value={approved} />
            <MiniMetric label="Pending" value={pending} />
            <MiniMetric label="Unreviewed" value={unreviewed} />
          </Flex>
        </Col>
        {categories.length > 0 && (
          <Col span={12}>
            <Flex vertical gap={6}>
              {categories.map((cat) => (
                <Flex key={cat.name} justify="space-between" align="center">
                  <Text className="text-xs">{cat.name}</Text>
                  <Flex align="center" gap={8}>
                    <Text type="secondary" className="text-xs">{cat.fieldCount} fields</Text>
                    <Text strong className="text-xs">{cat.approvedPercent}%</Text>
                  </Flex>
                </Flex>
              ))}
            </Flex>
          </Col>
        )}
      </Row>
    </Card>
  );
};

// --- Integrations (with Scopes header + button actions) ---

const IntegrationsSection = ({ system }: { system: MockSystem }) => (
  <div>
    <Flex justify="space-between" align="center">
      <Title level={4} className="!mb-0 !mt-0">Integrations</Title>
      <Button type="primary" size="small">+ Add integration</Button>
    </Flex>
    <Divider className="!mb-4 !mt-2" />
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

const ACTION_DOT_COLORS: Record<string, string> = {
  "Monitor completed": "#5a9a68",
  "Fields classified": "#5a9a68",
  "Steward assigned": "#4a90e2",
  "Purpose added": "#7b4ea9",
  "System registered": "#7b4ea9",
  "Integration added": "#7b4ea9",
  "Monitor created": "#7b4ea9",
  "Integration tested": "#e59d47",
};

const ActivitySection = ({ system }: { system: MockSystem }) => (
  <div className="max-h-[300px] overflow-y-auto">
    {system.history.length > 0 ? (
      <Flex vertical gap={0}>
        {system.history.map((entry, i) => (
          <Flex key={i} justify="space-between" align="center" className="border-b border-solid border-[#f5f5f5] py-2.5 last:border-b-0">
            <Flex align="center" gap={8} className="min-w-0 flex-1">
              <div
                className="size-[6px] shrink-0 rounded-full"
                style={{ backgroundColor: ACTION_DOT_COLORS[entry.action] ?? "#93969a" }}
              />
              <Flex vertical gap={1} className="min-w-0">
                <Text strong className="text-xs">{entry.action}</Text>
                <Text className="truncate text-xs">{entry.detail}</Text>
              </Flex>
            </Flex>
            <Flex align="center" gap={10} className="shrink-0 pl-4">
              <Avatar size={20} style={{ backgroundColor: "#e6e6e8", color: "#53575c", fontSize: 9 }}>{entry.user.slice(0, 2).toUpperCase()}</Avatar>
              <Text type="secondary" className="w-[70px] text-right text-[10px]">{new Date(entry.timestamp).toLocaleDateString()}</Text>
            </Flex>
          </Flex>
        ))}
      </Flex>
    ) : (
      <Text type="secondary" className="text-xs">No activity recorded</Text>
    )}
  </div>
);

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
    <Flex vertical gap={20}>
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
      <IntegrationsSection system={system} />
      <div>
        <SectionHeader title="Data & Monitoring" />
        <Row gutter={[24, 24]}>
          <Col span={12}><ProducerConsumerCard relationships={system.relationships} /></Col>
          <Col span={12}><MonitorsCard monitors={system.monitors} /></Col>
        </Row>
      </div>
      <div>
        <SectionHeader title="Activity" />
        <ActivitySection system={system} />
      </div>
    </Flex>
  );

  return (
    <Tabs
      items={[
        { key: "overview", label: "Overview", children: overviewContent },
        { key: "assets", label: "Assets", children: <AssetsContent system={system} /> },
        { key: "advanced", label: "Advanced", children: <AdvancedContent system={system} /> },
      ]}
      defaultActiveKey="overview"
    />
  );
};

export default SystemDetailContent;
