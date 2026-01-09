import {
  Button,
  Card,
  CUSTOM_TAG_COLOR,
  Flex,
  Input,
  Select,
  Space,
  Tag,
  Typography,
  PlusOutlined,
} from "fidesui";
// TODO: fix this export to be better encapsulated in fidesui
import palette from "fidesui/src/palette/palette.module.scss";
import {
  SearchOutlined,
  ArrowRightOutlined,
  FileTextOutlined,
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

const PrivacyAssessmentsPage: NextPage = () => {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");

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
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreateNew}
          >
            Create new assessment
          </Button>
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
    </Layout>
  );
};

export default PrivacyAssessmentsPage;
