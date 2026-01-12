import {
  Button,
  Card,
  CUSTOM_TAG_COLOR,
  Flex,
  Input,
  Modal,
  Select,
  Space,
  Tag,
  Typography,
  PlusOutlined,
  Checkbox,
  Upload,
} from "fidesui";
// TODO: fix this export to be better encapsulated in fidesui
import palette from "fidesui/src/palette/palette.module.scss";
import {
  SearchOutlined,
  ArrowRightOutlined,
  FileTextOutlined,
  SettingOutlined,
  CloudUploadOutlined,
} from "@ant-design/icons";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useState } from "react";

import Layout from "~/features/common/Layout";
import {
  PRIVACY_ASSESSMENTS_ROUTE,
  PRIVACY_ASSESSMENTS_ONBOARDING_ROUTE,
} from "~/features/common/nav/routes";
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
        status: "updated",
        statusTime: "1d ago",
        riskLevel: "Low",
        completeness: 90,
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
        status: "updated",
        statusTime: "5h ago",
        riskLevel: "Med",
        completeness: 80,
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
        status: "updated",
        statusTime: "4h ago",
        riskLevel: "Low",
        completeness: 85,
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
  { id: "gdpr", label: "GDPR", description: "General Data Protection Regulation (EU)" },
  { id: "ccpa", label: "CCPA / CPRA", description: "California Consumer Privacy Act" },
  { id: "hipaa", label: "HIPAA", description: "Health Insurance Portability Act" },
  { id: "nist", label: "NIST AI RMF", description: "AI Risk Management Framework" },
  { id: "eu-ai", label: "EU AI Act", description: "Artificial Intelligence Act" },
  { id: "iso", label: "ISO 42001", description: "AI Management System Standard" },
];

const regions = [
  "United States",
  "European Union",
  "United Kingdom",
  "Canada",
  "Brazil",
];

const PrivacyAssessmentsPage: NextPage = () => {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [selectedRegions, setSelectedRegions] = useState<string[]>(["United States", "European Union"]);
  const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>(["gdpr", "ccpa"]);
  const [regionSearch, setRegionSearch] = useState("");

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
      setSelectedFrameworks(selectedFrameworks.filter((f) => f !== frameworkId));
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
    router.push(`${PRIVACY_ASSESSMENTS_ROUTE}/onboarding`);
  };

  const handleAssessmentClick = (id: string) => {
    router.push(`${PRIVACY_ASSESSMENTS_ROUTE}/${id}`);
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
        <Tag color={colors[risk] || CUSTOM_TAG_COLOR.DEFAULT}>
          {risk} risk
        </Tag>
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
            />
          </Space>
        }
        isSticky={true}
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
          <Flex gap="middle" align="center" justify="space-between" wrap={false}>
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
                options={[
                  { label: "All", value: "all" },
                  { label: "Updated", value: "updated" },
                  { label: "Out of date", value: "outdated" },
                ]}
              />
              <Select
                placeholder="Framework: All"
                style={{ width: 280 }}
                options={[
                  { label: "All", value: "all" },
                  { label: "GDPR", value: "gdpr" },
                  { label: "CCPA", value: "ccpa" },
                ]}
              />
              <Select
                placeholder="Owner: Me"
                style={{ width: 240 }}
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
          {Object.entries(mockAssessments).map(([key, template]) => (
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
                <Button type="link" style={{ padding: 0 }}>
                  View all <ArrowRightOutlined style={{ fontSize: 12 }} />
                </Button>
              </Flex>

              <Flex gap="middle" wrap="wrap">
                {template.assessments.map((assessment) => (
                  <Card
                    key={assessment.id}
                    hoverable
                    style={{
                      width: "calc((100% - 48px) / 4)",
                      minWidth: 280,
                      cursor: "pointer",
                    }}
                    onClick={() => handleAssessmentClick(assessment.id)}
                  >
                    <Flex vertical gap="small">
                      <Title
                        level={5}
                        style={{
                          margin: 0,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {assessment.name}
                      </Title>
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
                      <div
                        style={{
                          marginTop: 16,
                          paddingTop: 16,
                          borderTop: "1px solid #f0f0f0",
                        }}
                      >
                        <Flex justify="space-between" style={{ marginBottom: 8 }}>
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
                            {getStatusText(assessment.status, assessment.statusTime) && (
                              <Text
                                style={{
                                  fontSize: 11,
                                  color: getStatusColor(assessment.status),
                                }}
                              >
                                {getStatusText(assessment.status, assessment.statusTime)}
                              </Text>
                            )}
                          </Flex>
                          <Button type="link" style={{ padding: 0, fontSize: 12 }}>
                            Resume
                          </Button>
                        </Flex>
                      </div>
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

      <Modal
        title="Assessment settings"
        open={isSettingsModalOpen}
        onCancel={() => setIsSettingsModalOpen(false)}
        onOk={() => setIsSettingsModalOpen(false)}
        okText="Save"
        width={800}
      >
        <Space direction="vertical" size="large" style={{ width: "100%", marginTop: 24 }}>
          <div style={{ padding: "16px", backgroundColor: palette.FIDESUI_BG_CORINTH, borderRadius: 8, marginBottom: 8 }}>
            <Text style={{ fontSize: 14, lineHeight: 1.6 }}>
              The selections you make here and any historical assessments you upload will be used to train our LLM to understand your organization's specific compliance needs, risk profile, and processing patterns. This enables the AI to generate more accurate and tailored privacy assessments.
            </Text>
          </div>
          <div>
            <Title level={4} style={{ marginBottom: 12 }}>
              Operational regions
            </Title>
            <Text type="secondary" style={{ marginBottom: 20, display: "block", fontSize: 12 }}>
              These regions determine jurisdictional priorities for AI risk analysis.
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
                } else if (regionSearch.trim() && !selectedRegions.includes(regionSearch.trim())) {
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
                    onClick={() => handleAddRegion(region)}
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
            <Flex justify="space-between" align="center" style={{ marginBottom: 12 }}>
              <Title level={4} style={{ margin: 0 }}>
                Target frameworks & regulations
              </Title>
              <Button type="link" onClick={handleSelectAllFrameworks} style={{ padding: 0 }}>
                {selectedFrameworks.length === frameworks.length ? "Deselect all" : "Select all"}
              </Button>
            </Flex>
            <Text type="secondary" style={{ marginBottom: 20, display: "block", fontSize: 12 }}>
              Select the privacy frameworks and regulations that apply to your organization.
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
                    <Checkbox checked={selectedFrameworks.includes(framework.id)} />
                  </Flex>
                </Card>
              ))}
            </Space>
          </div>

          <div>
            <Title level={4} style={{ marginBottom: 12 }}>
              Upload historical assessments
            </Title>
            <Text type="secondary" style={{ marginBottom: 20, display: "block", fontSize: 12 }}>
              Upload previous privacy assessments to help the AI understand your existing compliance posture.
            </Text>
            <Upload.Dragger
              multiple
              beforeUpload={() => false}
              style={{ padding: 20 }}
            >
              <p>
                <CloudUploadOutlined style={{ fontSize: 48, color: "#1890ff" }} />
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
