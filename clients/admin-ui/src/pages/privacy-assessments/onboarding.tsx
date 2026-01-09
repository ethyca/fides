import {
  Button,
  Card,
  Checkbox,
  Flex,
  Input,
  Space,
  Tag,
  Typography,
  Upload,
} from "fidesui";
import {
  SearchOutlined,
  CloudUploadOutlined,
} from "@ant-design/icons";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useState } from "react";

import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

const { Title, Text } = Typography;

const ONBOARDING_COMPLETE_KEY = "privacy-assessments-onboarding-complete";

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

const PrivacyAssessmentsOnboardingPage: NextPage = () => {
  const router = useRouter();
  const [selectedRegions, setSelectedRegions] = useState<string[]>([]);
  const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>([]);
  const [regionSearch, setRegionSearch] = useState("");

  const handleSave = () => {
    localStorage.setItem(ONBOARDING_COMPLETE_KEY, "true");
    router.push(PRIVACY_ASSESSMENTS_ROUTE);
  };

  const handleCancel = () => {
    router.push(PRIVACY_ASSESSMENTS_ROUTE);
  };

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

  const filteredRegions = regions.filter(
    (region) =>
      !selectedRegions.includes(region) &&
      region.toLowerCase().includes(regionSearch.toLowerCase()),
  );

  return (
    <Layout title="Privacy assessments setup">
      <PageHeader
        heading="Privacy assessments"
        breadcrumbItems={[
          { title: "Privacy assessments", href: PRIVACY_ASSESSMENTS_ROUTE },
          { title: "Setup" },
        ]}
      />
      <div style={{ padding: "40px", display: "flex", justifyContent: "center" }}>
        <div style={{ maxWidth: 900, width: "100%" }}>
          <Space direction="vertical" size="large" style={{ width: "100%" }}>
            <div style={{ textAlign: "center", marginBottom: 32 }}>
              <Title level={2} style={{ marginBottom: 8 }}>
                Welcome to Privacy Assessments
              </Title>
              <Text type="secondary" style={{ fontSize: 16 }}>
                Configure your global privacy preferences to tailor AI assessments for your compliance needs
              </Text>
            </div>

            <Card
              style={{
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.15)",
                borderRadius: 8,
              }}
            >
              <Space direction="vertical" size="large" style={{ width: "100%" }}>
                <div>
                  <Title level={4} style={{ marginBottom: 8 }}>
                    Operational Regions
                  </Title>
                  <Text type="secondary" style={{ marginBottom: 16, display: "block", fontSize: 12 }}>
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
                    <div
                      style={{
                        border: "1px solid #e5e7eb",
                        borderRadius: 4,
                        maxHeight: 200,
                        overflow: "auto",
                        marginTop: 8,
                      }}
                    >
                      {filteredRegions.map((region) => (
                        <div
                          key={region}
                          onClick={() => handleAddRegion(region)}
                          style={{
                            padding: "8px 12px",
                            cursor: "pointer",
                            borderBottom: "1px solid #f0f0f0",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.backgroundColor = "#f5f5f5";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = "white";
                          }}
                        >
                          {region}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </Space>
            </Card>

            <Card
              style={{
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.15)",
                borderRadius: 8,
              }}
            >
              <Space direction="vertical" size="large" style={{ width: "100%" }}>
                <div>
                  <Flex justify="space-between" align="center" style={{ marginBottom: 8 }}>
                    <Title level={4} style={{ margin: 0 }}>
                      Target Frameworks & Regulations
                    </Title>
                    <Button type="link" onClick={handleSelectAllFrameworks} style={{ padding: 0 }}>
                      Select all that apply
                    </Button>
                  </Flex>
                  <Flex gap="middle" wrap style={{ marginTop: 16 }}>
                    {frameworks.map((framework) => (
                      <Card
                        key={framework.id}
                        style={{
                          width: "calc((100% - 64px) / 3)",
                          minWidth: 280,
                          border: "1px solid #e5e7eb",
                          boxShadow: "0 1px 2px rgba(0, 0, 0, 0.08)",
                        }}
                      >
                        <Checkbox
                          checked={selectedFrameworks.includes(framework.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedFrameworks([...selectedFrameworks, framework.id]);
                            } else {
                              setSelectedFrameworks(
                                selectedFrameworks.filter((f) => f !== framework.id),
                              );
                            }
                          }}
                          style={{ width: "100%" }}
                        >
                          <Flex vertical gap="small" style={{ marginLeft: 8 }}>
                            <Text strong style={{ fontSize: 14 }}>
                              {framework.label}
                            </Text>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              {framework.description}
                            </Text>
                          </Flex>
                        </Checkbox>
                      </Card>
                    ))}
                  </Flex>
                </div>
              </Space>
            </Card>

            <Card
              style={{
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.15)",
                borderRadius: 8,
              }}
            >
              <Space direction="vertical" size="large" style={{ width: "100%" }}>
                <div>
                  <Flex justify="space-between" align="center" style={{ marginBottom: 8 }}>
                    <Title level={4} style={{ margin: 0 }}>
                      Upload Historical Assessments
                    </Title>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Optional
                    </Text>
                  </Flex>
                  <Text type="secondary" style={{ marginBottom: 16, display: "block", fontSize: 12 }}>
                    Upload previous assessments to help the AI learn your organization's specific writing style, tone, and formatting preferences.
                  </Text>
                  <Upload.Dragger>
                    <p>
                      <CloudUploadOutlined style={{ fontSize: 48, color: "#9ca3af" }} />
                    </p>
                    <p style={{ marginTop: 16 }}>
                      <Text strong>Click to upload or drag and drop</Text>
                    </p>
                    <p>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        PDF or DOCX (max. 10MB)
                      </Text>
                    </p>
                  </Upload.Dragger>
              </div>
            </Space>
          </Card>

          <Flex justify="flex-end" gap="middle" style={{ marginTop: 32 }}>
            <Button onClick={handleCancel} size="large">
              Cancel
            </Button>
            <Button type="primary" onClick={handleSave} size="large">
              Save
            </Button>
          </Flex>
          </Space>
        </div>
      </div>
    </Layout>
  );
};

export default PrivacyAssessmentsOnboardingPage;
