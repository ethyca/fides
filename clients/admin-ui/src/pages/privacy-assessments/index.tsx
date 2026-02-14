import {
  CloudUploadOutlined,
  FileTextOutlined,
  SearchOutlined,
  SettingOutlined,
  SlackOutlined,
} from "@ant-design/icons";
import {
  Button,
  Card,
  Checkbox,
  CUSTOM_TAG_COLOR,
  Flex,
  Input,
  Modal,
  PlusOutlined,
  Result,
  Select,
  Space,
  Tag,
  Tooltip,
  Typography,
  Upload,
} from "fidesui";
// TODO: fix this export to be better encapsulated in fidesui
import palette from "fidesui/src/palette/palette.module.scss";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

const { Title, Text } = Typography;

// Mock data for assessments
const mockAssessments = {
  gdpr: {
    templateId: "GDPR-DPIA-2024",
    title: "GDPR Data Protection Impact Assessment",
    assessments: [
      {
        id: "1",
        name: "Customer Insight AI Module",
        status: "updated",
        statusTime: "2h ago",
        riskLevel: "High",
        completeness: 75,
        owner: "SJ",
      },
      {
        id: "2",
        name: "Employee Monitoring Tool",
        status: "outdated",
        riskLevel: "Med",
        completeness: 40,
        owner: "MP",
      },
      {
        id: "3",
        name: "Marketing Analytics Platform",
        status: "completed",
        statusTime: "Jan 15, 2024",
        riskLevel: "Low",
        completeness: 100,
        owner: "AL",
      },
      {
        id: "4",
        name: "Customer Support Chat System",
        status: "updated",
        statusTime: "3h ago",
        riskLevel: "Med",
        completeness: 65,
        owner: "SJ",
      },
      {
        id: "5",
        name: "HR Payroll Processing",
        status: "outdated",
        riskLevel: "High",
        completeness: 30,
        owner: "MP",
      },
      {
        id: "6",
        name: "E-commerce Recommendation Engine",
        status: "completed",
        statusTime: "Jan 12, 2024",
        riskLevel: "Med",
        completeness: 100,
        owner: "AL",
      },
    ],
  },
  ccpa: {
    templateId: "CCPA-PIA-2024",
    title: "CCPA Privacy Impact Assessment",
    assessments: [
      {
        id: "7",
        name: "Consumer Data Collection System",
        status: "updated",
        statusTime: "1h ago",
        riskLevel: "High",
        completeness: 70,
        owner: "SJ",
      },
      {
        id: "8",
        name: "Third-Party Data Sharing Platform",
        status: "outdated",
        riskLevel: "Med",
        completeness: 45,
        owner: "MP",
      },
      {
        id: "9",
        name: "Opt-Out Request Handler",
        status: "completed",
        statusTime: "Jan 10, 2024",
        riskLevel: "Low",
        completeness: 100,
        owner: "AL",
      },
      {
        id: "10",
        name: "Data Broker Integration",
        status: "outdated",
        riskLevel: "High",
        completeness: 25,
        owner: "SJ",
      },
    ],
  },
};

const frameworks = [
  {
    id: "gdpr",
    label: "GDPR",
    description: "General Data Protection Regulation (EU)",
  },
  {
    id: "ccpa",
    label: "CCPA / CPRA",
    description: "California Consumer Privacy Act",
  },
  {
    id: "hipaa",
    label: "HIPAA",
    description: "Health Insurance Portability Act",
  },
  {
    id: "nist",
    label: "NIST AI RMF",
    description: "AI Risk Management Framework",
  },
  {
    id: "eu-ai",
    label: "EU AI Act",
    description: "Artificial Intelligence Act",
  },
  {
    id: "iso",
    label: "ISO 42001",
    description: "AI Management System Standard",
  },
];

const regions = [
  "United States",
  "European Union",
  "United Kingdom",
  "Canada",
  "Brazil",
];

const dpoOptions = [
  { id: "jd", name: "Jane Doe", role: "Data Protection Officer" },
  { id: "sj", name: "Sarah Johnson", role: "Privacy Lead" },
  { id: "mp", name: "Michael Park", role: "Compliance Manager" },
  { id: "al", name: "Anna Lee", role: "Legal Counsel" },
];

const VIEWED_ASSESSMENTS_KEY = "privacy-assessments-viewed";

const PrivacyAssessmentsPage: NextPage = () => {
  const { flags } = useFeatures();
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [selectedRegions, setSelectedRegions] = useState<string[]>([
    "United States",
    "European Union",
  ]);
  const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>([
    "gdpr",
    "ccpa",
  ]);
  const [regionSearch, setRegionSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [viewedAssessments, setViewedAssessments] = useState<Set<string>>(
    new Set(),
  );

  // Create assessment modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newAssessment, setNewAssessment] = useState({
    name: "",
    framework: "gdpr",
    dpo: "",
    description: "",
    systemName: "",
  });
  const [assessments, setAssessments] = useState(mockAssessments);

  // Load viewed assessments from localStorage on mount
  // Initialize with half of assessments already viewed (so half are "new")
  useEffect(() => {
    const getAllAssessmentIds = () => {
      return [
        ...mockAssessments.gdpr.assessments.map((a) => a.id),
        ...mockAssessments.ccpa.assessments.map((a) => a.id),
      ];
    };

    const stored = localStorage.getItem(VIEWED_ASSESSMENTS_KEY);
    if (stored) {
      try {
        const viewedIds = JSON.parse(stored) as string[];
        setViewedAssessments(new Set(viewedIds));
      } catch {
        // If parsing fails, initialize with half viewed
        const allAssessmentIds = getAllAssessmentIds();
        const halfViewed = allAssessmentIds.slice(
          0,
          Math.ceil(allAssessmentIds.length / 2),
        );
        setViewedAssessments(new Set(halfViewed));
        localStorage.setItem(
          VIEWED_ASSESSMENTS_KEY,
          JSON.stringify(halfViewed),
        );
      }
    } else {
      // First time: initialize with half viewed
      const allAssessmentIds = getAllAssessmentIds();
      const halfViewed = allAssessmentIds.slice(
        0,
        Math.ceil(allAssessmentIds.length / 2),
      );
      setViewedAssessments(new Set(halfViewed));
      localStorage.setItem(VIEWED_ASSESSMENTS_KEY, JSON.stringify(halfViewed));
    }
  }, []);

  // Check feature flag after all hooks
  if (!flags?.alphaDataProtectionAssessments) {
    return (
      <Layout title="Privacy Assessments">
        <Result
          status="error"
          title="Feature not available"
          subTitle="This feature is currently behind a feature flag and is not enabled."
        />
      </Layout>
    );
  }

  const handleAddRegion = (region: string) => {
    if (!selectedRegions.includes(region)) {
      setSelectedRegions([...selectedRegions, region]);
    }
    setRegionSearch("");
  };

  const handleRemoveRegion = (region: string) => {
    setSelectedRegions(selectedRegions.filter((r) => r !== region));
  };

  const handleSelectAllFrameworks = () => {
    if (selectedFrameworks.length === frameworks.length) {
      setSelectedFrameworks([]);
    } else {
      setSelectedFrameworks(frameworks.map((f) => f.id));
    }
  };

  const handleToggleFramework = (frameworkId: string) => {
    if (selectedFrameworks.includes(frameworkId)) {
      setSelectedFrameworks(
        selectedFrameworks.filter((f) => f !== frameworkId),
      );
    } else {
      setSelectedFrameworks([...selectedFrameworks, frameworkId]);
    }
  };

  const filteredRegions = regions.filter(
    (region) =>
      !selectedRegions.includes(region) &&
      region.toLowerCase().includes(regionSearch.toLowerCase()),
  );

  const handleCreateNew = () => {
    setIsCreateModalOpen(true);
  };

  const handleCreateAssessment = () => {
    if (!newAssessment.name || !newAssessment.dpo) {
      return;
    }

    const newId = String(Date.now());
    const dpoInfo = dpoOptions.find((d) => d.id === newAssessment.dpo);
    const newAssessmentData = {
      id: newId,
      name: newAssessment.name,
      status: "updated" as const,
      statusTime: "Just now",
      riskLevel: "TBD",
      completeness: 0,
      owner:
        dpoInfo?.name
          .split(" ")
          .map((n) => n[0])
          .join("") ?? "??",
    };

    // Add to the selected framework's assessments
    setAssessments((prev) => ({
      ...prev,
      [newAssessment.framework]: {
        ...prev[newAssessment.framework as keyof typeof prev],
        assessments: [
          newAssessmentData,
          ...prev[newAssessment.framework as keyof typeof prev].assessments,
        ],
      },
    }));

    setIsCreateModalOpen(false);
    // Reset form
    setNewAssessment({
      name: "",
      framework: "gdpr",
      dpo: "",
      description: "",
      systemName: "",
    });
  };

  const handleAssessmentClick = (id: string) => {
    // Mark assessment as viewed
    const newViewed = new Set(viewedAssessments);
    newViewed.add(id);
    setViewedAssessments(newViewed);
    localStorage.setItem(
      VIEWED_ASSESSMENTS_KEY,
      JSON.stringify(Array.from(newViewed)),
    );

    router.push(`${PRIVACY_ASSESSMENTS_ROUTE}/${id}`);
  };

  const isNewAssessment = (id: string) => {
    return !viewedAssessments.has(id);
  };

  const getStatusText = (status: string, time?: string) => {
    if (status === "updated") {
      return `Updated${time ? ` • ${time}` : ""}`;
    }
    if (status === "outdated") {
      return "Out of date";
    }
    return null;
  };

  const getStatusColor = (status: string) => {
    if (status === "updated") {
      return palette.FIDESUI_SUCCESS;
    }
    if (status === "outdated") {
      return palette.FIDESUI_ERROR;
    }
    return undefined;
  };

  const getRiskTag = (risk: string) => {
    const colors: Record<string, CUSTOM_TAG_COLOR> = {
      High: CUSTOM_TAG_COLOR.ERROR,
      Med: CUSTOM_TAG_COLOR.WARNING,
      Low: CUSTOM_TAG_COLOR.DEFAULT,
    };
    return (
      <div style={{ display: "inline-block" }}>
        <Tag color={colors[risk] ?? CUSTOM_TAG_COLOR.DEFAULT}>{risk} risk</Tag>
      </div>
    );
  };

  return (
    <Layout title="Privacy assessments">
      <PageHeader
        heading="Privacy assessments"
        breadcrumbItems={[{ title: "Privacy assessments" }]}
        rightContent={
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreateNew}
            >
              Create new assessment
            </Button>
            <Button
              icon={<SettingOutlined />}
              onClick={() => setIsSettingsModalOpen(true)}
              aria-label="Settings"
            />
          </Space>
        }
        isSticky
      >
        <Text type="secondary" style={{ fontSize: 14 }}>
          Manage compliance documentation grouped by template type.
        </Text>
        <div
          style={{
            paddingTop: "16px",
            paddingBottom: "16px",
            borderTop: "1px solid #f0f0f0",
            marginTop: "16px",
          }}
        >
          <Flex
            gap="middle"
            align="center"
            justify="space-between"
            wrap={false}
          >
            <Input
              placeholder="Search templates or assessments..."
              prefix={<SearchOutlined />}
              style={{ flex: 1, maxWidth: 400 }}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <Flex gap="middle" align="center">
              <Select
                placeholder="Status: All"
                style={{ width: 240 }}
                value={statusFilter === "all" ? undefined : statusFilter}
                onChange={(value) => setStatusFilter(value || "all")}
                allowClear
                aria-label="Filter by status"
                options={[
                  { label: "Status: New", value: "new" },
                  { label: "Status: Completed", value: "completed" },
                  { label: "Status: Updated", value: "updated" },
                  { label: "Status: Out of date", value: "outdated" },
                ]}
              />
              <Select
                placeholder="Framework: All"
                style={{ width: 280 }}
                aria-label="Filter by framework"
                options={[
                  { label: "All", value: "all" },
                  { label: "GDPR", value: "gdpr" },
                  { label: "CCPA", value: "ccpa" },
                ]}
              />
              <Select
                placeholder="Owner: Me"
                style={{ width: 240 }}
                aria-label="Filter by owner"
                options={[
                  { label: "Me", value: "me" },
                  { label: "All", value: "all" },
                ]}
              />
            </Flex>
          </Flex>
        </div>
      </PageHeader>
      <div style={{ padding: "24px 40px" }}>
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          {Object.entries(assessments).map(([key, template]) => (
            <div key={key}>
              <Flex
                justify="space-between"
                align="flex-end"
                style={{
                  marginBottom: 16,
                  paddingBottom: 8,
                  borderBottom: "1px solid #e5e7eb",
                }}
              >
                <Flex gap="middle" align="center">
                  <div
                    style={{
                      width: 40,
                      height: 40,
                      border: "1px solid #e5e7eb",
                      borderRadius: 4,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <FileTextOutlined />
                  </div>
                  <div>
                    <Title level={4} style={{ margin: 0 }}>
                      {template.title}
                    </Title>
                    <Text type="secondary" style={{ fontSize: 14 }}>
                      Template ID: {template.templateId} •{" "}
                      {template.assessments.length} active assessments
                    </Text>
                  </div>
                </Flex>
              </Flex>

              <Flex gap="middle" wrap="wrap">
                {template.assessments
                  .filter((assessment) => {
                    if (statusFilter === "all") {
                      return true;
                    }
                    if (statusFilter === "new") {
                      return isNewAssessment(assessment.id);
                    }
                    if (statusFilter === "completed") {
                      return assessment.status === "completed";
                    }
                    if (statusFilter === "updated") {
                      return assessment.status === "updated";
                    }
                    if (statusFilter === "outdated") {
                      return assessment.status === "outdated";
                    }
                    return true;
                  })
                  .map((assessment) => (
                    <Card
                      key={assessment.id}
                      hoverable
                      style={{
                        width: "calc((100% - 48px) / 4)",
                        minWidth: 280,
                        cursor: "pointer",
                        ...(assessment.completeness === 100 && {
                          borderLeft: `4px solid ${palette.FIDESUI_SUCCESS}`,
                        }),
                      }}
                      onClick={() => handleAssessmentClick(assessment.id)}
                    >
                      <Flex vertical gap="small">
                        <Flex
                          justify="space-between"
                          align="flex-start"
                          gap="small"
                        >
                          <Title
                            level={5}
                            style={{
                              margin: 0,
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                              flex: 1,
                            }}
                          >
                            {assessment.name}
                          </Title>
                          {isNewAssessment(assessment.id) &&
                            assessment.completeness < 100 && (
                              <Flex
                                align="center"
                                gap="small"
                                style={{
                                  flexShrink: 0,
                                  fontSize: 11,
                                  color: palette.FIDESUI_NEUTRAL_600,
                                }}
                              >
                                <div
                                  style={{
                                    width: 6,
                                    height: 6,
                                    borderRadius: "50%",
                                    backgroundColor: palette.FIDESUI_SUCCESS,
                                  }}
                                />
                                <Text style={{ fontSize: 11 }}>New</Text>
                              </Flex>
                            )}
                        </Flex>
                        <Text
                          type="secondary"
                          style={{
                            fontSize: 14,
                            display: "-webkit-box",
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: "vertical",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                          }}
                        >
                          Evaluation of data processing activities.
                        </Text>
                        {getRiskTag(assessment.riskLevel)}
                        {/* Completed assessment style */}
                        {assessment.completeness === 100 && (
                          <div
                            style={{
                              marginTop: 16,
                              paddingTop: 16,
                              borderTop: "1px solid #f0f0f0",
                            }}
                          >
                            <Flex
                              align="center"
                              gap="middle"
                              style={{
                                padding: "12px",
                                backgroundColor: `${palette.FIDESUI_SUCCESS}10`,
                                borderRadius: 8,
                              }}
                            >
                              <div
                                style={{
                                  width: 28,
                                  height: 28,
                                  borderRadius: "50%",
                                  backgroundColor: palette.FIDESUI_SUCCESS,
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                }}
                              >
                                <svg
                                  width="14"
                                  height="14"
                                  viewBox="0 0 32 32"
                                  fill="none"
                                  xmlns="http://www.w3.org/2000/svg"
                                >
                                  <path
                                    d="M13 24L4 15L6.5 12.5L13 19L25.5 6.5L28 9L13 24Z"
                                    fill="white"
                                  />
                                </svg>
                              </div>
                              <div>
                                <Text
                                  strong
                                  style={{
                                    fontSize: 14,
                                    display: "block",
                                    color: palette.FIDESUI_SUCCESS,
                                  }}
                                >
                                  Assessment complete
                                </Text>
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                  Updated {assessment.statusTime}
                                </Text>
                              </div>
                            </Flex>
                          </div>
                        )}
                        {/* In-progress assessment (default) */}
                        {assessment.completeness < 100 && (
                          <div
                            style={{
                              marginTop: 16,
                              paddingTop: 16,
                              borderTop: "1px solid #f0f0f0",
                            }}
                          >
                            <Flex
                              justify="space-between"
                              style={{ marginBottom: 8 }}
                            >
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                Completeness
                              </Text>
                              <Text strong style={{ fontSize: 12 }}>
                                {assessment.completeness}%
                              </Text>
                            </Flex>
                            <div
                              style={{
                                height: 6,
                                backgroundColor: "#f0f0f0",
                                borderRadius: 3,
                                overflow: "hidden",
                              }}
                            >
                              <div
                                style={{
                                  height: "100%",
                                  width: `${assessment.completeness}%`,
                                  backgroundColor: palette.FIDESUI_MINOS,
                                }}
                              />
                            </div>
                            <Flex
                              justify="space-between"
                              align="center"
                              style={{ marginTop: 8 }}
                            >
                              <Flex align="center" gap="small">
                                <div
                                  style={{
                                    width: 20,
                                    height: 20,
                                    borderRadius: "50%",
                                    backgroundColor: palette.FIDESUI_MINOS,
                                    color: "white",
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    fontSize: 10,
                                    fontWeight: 700,
                                  }}
                                >
                                  {assessment.owner}
                                </div>
                                {getStatusText(
                                  assessment.status,
                                  assessment.statusTime,
                                ) && (
                                  <Text
                                    style={{
                                      fontSize: 11,
                                      color: getStatusColor(assessment.status),
                                    }}
                                  >
                                    {getStatusText(
                                      assessment.status,
                                      assessment.statusTime,
                                    )}
                                  </Text>
                                )}
                              </Flex>
                              <Flex align="center" gap="small">
                                <Tooltip title="Request input from your team via Slack">
                                  <Button
                                    type="text"
                                    icon={<SlackOutlined />}
                                    size="small"
                                    aria-label="Request input via Slack"
                                    style={{
                                      padding: "4px 8px",
                                      color: palette.FIDESUI_NEUTRAL_600,
                                    }}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      // Handle Slack conversation initiation
                                    }}
                                  />
                                </Tooltip>
                                <Button
                                  type="link"
                                  style={{ padding: 0, fontSize: 12 }}
                                >
                                  Resume
                                </Button>
                              </Flex>
                            </Flex>
                          </div>
                        )}
                      </Flex>
                    </Card>
                  ))}
                <Card
                  hoverable
                  style={{
                    width: "calc((100% - 48px) / 4)",
                    minWidth: 280,
                    border: "1px dashed #d9d9d9",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    minHeight: 200,
                    cursor: "pointer",
                  }}
                  onClick={handleCreateNew}
                >
                  <Flex vertical align="center" gap="small">
                    <PlusOutlined style={{ fontSize: 32, color: "#9ca3af" }} />
                    <Text strong style={{ color: "#4a4a4a" }}>
                      Start new assessment from this template
                    </Text>
                  </Flex>
                </Card>
              </Flex>
            </div>
          ))}
        </Space>
      </div>

      {/* Create Assessment Modal */}
      <Modal
        title="Create new assessment"
        open={isCreateModalOpen}
        onCancel={() => {
          setIsCreateModalOpen(false);
          setNewAssessment({
            name: "",
            framework: "gdpr",
            dpo: "",
            description: "",
            systemName: "",
          });
        }}
        onOk={handleCreateAssessment}
        okText="Create assessment"
        okButtonProps={{ disabled: !newAssessment.name || !newAssessment.dpo }}
        width={600}
      >
        <div
          style={{
            padding: "12px 16px",
            backgroundColor: palette.FIDESUI_BG_CORINTH,
            borderRadius: 8,
            marginBottom: 16,
          }}
        >
          <Text style={{ fontSize: 13, color: palette.FIDESUI_MINOS }}>
            Your assessment will be pre-populated with data from your Fides data
            map, including system details, data categories, and processing
            purposes to give you a head start.
          </Text>
        </div>
        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          <div>
            <Text strong style={{ display: "block", marginBottom: 8 }}>
              Assessment name <span style={{ color: "red" }}>*</span>
            </Text>
            <Input
              placeholder="e.g., Customer Data Processing Assessment"
              value={newAssessment.name}
              onChange={(e) =>
                setNewAssessment((prev) => ({ ...prev, name: e.target.value }))
              }
            />
          </div>

          <div>
            <Text strong style={{ display: "block", marginBottom: 8 }}>
              Framework / Template <span style={{ color: "red" }}>*</span>
            </Text>
            <Select
              style={{ width: "100%" }}
              aria-label="Select framework"
              value={newAssessment.framework}
              onChange={(value) =>
                setNewAssessment((prev) => ({ ...prev, framework: value }))
              }
              options={frameworks.map((f) => ({
                value: f.id,
                label: `${f.label} - ${f.description}`,
              }))}
            />
          </div>

          <div>
            <Text strong style={{ display: "block", marginBottom: 8 }}>
              Assigned DPO / Owner <span style={{ color: "red" }}>*</span>
            </Text>
            <Select
              style={{ width: "100%" }}
              aria-label="Select DPO or owner"
              placeholder="Select a DPO or owner"
              value={newAssessment.dpo || undefined}
              onChange={(value) =>
                setNewAssessment((prev) => ({ ...prev, dpo: value }))
              }
              options={dpoOptions.map((d) => ({
                value: d.id,
                label: `${d.name} - ${d.role}`,
              }))}
            />
          </div>

          <div>
            <Text strong style={{ display: "block", marginBottom: 8 }}>
              System or processing activity
            </Text>
            <Input
              placeholder="e.g., Marketing Analytics Platform"
              value={newAssessment.systemName}
              onChange={(e) =>
                setNewAssessment((prev) => ({
                  ...prev,
                  systemName: e.target.value,
                }))
              }
            />
          </div>

          <div>
            <Text strong style={{ display: "block", marginBottom: 8 }}>
              Description
            </Text>
            <Input.TextArea
              placeholder="Brief description of the assessment purpose..."
              rows={3}
              value={newAssessment.description}
              onChange={(e) =>
                setNewAssessment((prev) => ({
                  ...prev,
                  description: e.target.value,
                }))
              }
            />
          </div>
        </Space>
      </Modal>

      <Modal
        title="Assessment settings"
        open={isSettingsModalOpen}
        onCancel={() => setIsSettingsModalOpen(false)}
        onOk={() => setIsSettingsModalOpen(false)}
        okText="Save"
        width={800}
      >
        <Space
          direction="vertical"
          size="large"
          style={{ width: "100%", marginTop: 24 }}
        >
          <div
            style={{
              padding: "16px",
              backgroundColor: palette.FIDESUI_BG_CORINTH,
              borderRadius: 8,
              marginBottom: 8,
            }}
          >
            <Text style={{ fontSize: 14, lineHeight: 1.6 }}>
              The selections you make here and any historical assessments you
              upload will be used to train our LLM to understand your
              organization&apos;s specific compliance needs, risk profile, and
              processing patterns. This enables the AI to generate more accurate
              and tailored privacy assessments.
            </Text>
          </div>
          <div>
            <Title level={4} style={{ marginBottom: 12 }}>
              Operational regions
            </Title>
            <Text
              type="secondary"
              style={{ marginBottom: 20, display: "block", fontSize: 12 }}
            >
              These regions determine jurisdictional priorities for AI risk
              analysis.
            </Text>
            {selectedRegions.length > 0 && (
              <Flex gap="small" wrap style={{ marginBottom: 16 }}>
                {selectedRegions.map((region) => (
                  <Tag
                    key={region}
                    closable
                    onClose={() => handleRemoveRegion(region)}
                  >
                    {region}
                  </Tag>
                ))}
              </Flex>
            )}
            <Input
              placeholder="Search or add countries..."
              prefix={<SearchOutlined />}
              value={regionSearch}
              onChange={(e) => setRegionSearch(e.target.value)}
              onPressEnter={() => {
                if (filteredRegions.length > 0) {
                  handleAddRegion(filteredRegions[0]);
                } else if (
                  regionSearch.trim() &&
                  !selectedRegions.includes(regionSearch.trim())
                ) {
                  handleAddRegion(regionSearch.trim());
                }
              }}
              style={{ marginBottom: 8 }}
            />
            {regionSearch && filteredRegions.length > 0 && (
              <div style={{ marginTop: 8 }}>
                {filteredRegions.slice(0, 5).map((region) => (
                  <div
                    key={region}
                    role="button"
                    tabIndex={0}
                    onClick={() => handleAddRegion(region)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        handleAddRegion(region);
                      }
                    }}
                    style={{
                      padding: "8px 12px",
                      cursor: "pointer",
                      borderBottom: "1px solid #f0f0f0",
                    }}
                  >
                    {region}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <Flex
              justify="space-between"
              align="center"
              style={{ marginBottom: 12 }}
            >
              <Title level={4} style={{ margin: 0 }}>
                Target frameworks & regulations
              </Title>
              <Button
                type="link"
                onClick={handleSelectAllFrameworks}
                style={{ padding: 0 }}
              >
                {selectedFrameworks.length === frameworks.length
                  ? "Deselect all"
                  : "Select all"}
              </Button>
            </Flex>
            <Text
              type="secondary"
              style={{ marginBottom: 20, display: "block", fontSize: 12 }}
            >
              Select the privacy frameworks and regulations that apply to your
              organization.
            </Text>
            <Space direction="vertical" size="small" style={{ width: "100%" }}>
              {frameworks.map((framework) => (
                <Card
                  key={framework.id}
                  hoverable
                  style={{
                    border: selectedFrameworks.includes(framework.id)
                      ? `2px solid ${palette.FIDESUI_MINOS}`
                      : "1px solid #d9d9d9",
                    cursor: "pointer",
                  }}
                  onClick={() => handleToggleFramework(framework.id)}
                >
                  <Flex justify="space-between" align="center">
                    <div>
                      <Text strong>{framework.label}</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {framework.description}
                      </Text>
                    </div>
                    <Checkbox
                      checked={selectedFrameworks.includes(framework.id)}
                    />
                  </Flex>
                </Card>
              ))}
            </Space>
          </div>

          <div>
            <Title level={4} style={{ marginBottom: 12 }}>
              Upload historical assessments
            </Title>
            <Text
              type="secondary"
              style={{ marginBottom: 20, display: "block", fontSize: 12 }}
            >
              Upload previous privacy assessments to help the AI understand your
              existing compliance posture.
            </Text>
            <Upload.Dragger
              multiple
              beforeUpload={() => false}
              style={{ padding: 20 }}
            >
              <p>
                <CloudUploadOutlined
                  style={{ fontSize: 48, color: "#1890ff" }}
                />
              </p>
              <Text type="secondary" style={{ display: "block", marginTop: 8 }}>
                Click or drag files to this area to upload
              </Text>
              <Text type="secondary" style={{ fontSize: 12, marginTop: 4 }}>
                Support for PDF, DOCX, or CSV files
              </Text>
            </Upload.Dragger>
          </div>
        </Space>
      </Modal>
    </Layout>
  );
};

export default PrivacyAssessmentsPage;
