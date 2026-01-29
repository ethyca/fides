import { FileTextOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  CUSTOM_TAG_COLOR,
  Flex,
  PlusOutlined,
  Result,
  Space,
  Tag,
  Typography,
  useChakraToast as useToast,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { DEFAULT_TOAST_PARAMS, successToastParams } from "~/features/common/toast";

const { Title, Text } = Typography;

// Assessments to add when generating (based on Fides demo privacy declarations)
const generatedAssessments = {
  cpra: {
    templateId: "CPRA-RA-2024",
    title: "California CPRA Risk Assessment",
    assessments: [
      {
        id: "analyze_customer_behaviour",
        name: "Analyze customer behaviour for improvements",
        status: "updated",
        statusTime: "Just now",
        riskLevel: "Med",
        completeness: 53,
        system: "Demo Analytics System",
        dataCategories: ["user.contact", "user.device.cookie_id"],
        dataUse: "functional.service.improve",
      },
      {
        id: "collect_data_for_marketing",
        name: "Collect data for marketing",
        status: "updated",
        statusTime: "Just now",
        riskLevel: "High",
        completeness: 53,
        system: "Demo Marketing System",
        dataCategories: ["user.device.cookie_id"],
        dataUse: "marketing.advertising",
      },
    ],
  },
};

type AssessmentData = typeof generatedAssessments;

const ASSESSMENTS_STORAGE_KEY = "privacy-assessments-data";

const EmptyState = ({
  onGenerate,
  isGenerating,
}: {
  onGenerate: () => void;
  isGenerating: boolean;
}) => (
  <Flex
    vertical
    align="center"
    justify="center"
    style={{
      padding: "80px 40px",
      textAlign: "center",
    }}
  >
    <div
      style={{
        width: 64,
        height: 64,
        borderRadius: 8,
        backgroundColor: "#f5f5f5",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        marginBottom: 24,
      }}
    >
      <FileTextOutlined style={{ fontSize: 32, color: "#9ca3af" }} />
    </div>
    <Title level={4} style={{ margin: 0, marginBottom: 8 }}>
      No privacy assessments yet
    </Title>
    <Text
      type="secondary"
      style={{
        fontSize: 14,
        maxWidth: 400,
        marginBottom: 24,
        display: "block",
      }}
    >
      Generate privacy assessments to evaluate your systems against regulatory
      frameworks and identify compliance gaps.
    </Text>
    <Button
      type="primary"
      icon={<PlusOutlined />}
      onClick={onGenerate}
      loading={isGenerating}
      disabled={isGenerating}
    >
      {isGenerating ? "Generating..." : "Generate privacy assessments"}
    </Button>
  </Flex>
);

const PrivacyAssessmentsPage: NextPage = () => {
  const { flags } = useFeatures();
  const router = useRouter();
  const toast = useToast();
  const [assessments, setAssessments] = useState<AssessmentData | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  // Load assessments from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(ASSESSMENTS_STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as AssessmentData;
        setAssessments(parsed);
      } catch {
        // Invalid data, ignore
      }
    }
  }, []);

  // Save assessments to localStorage when they change
  useEffect(() => {
    if (assessments) {
      localStorage.setItem(ASSESSMENTS_STORAGE_KEY, JSON.stringify(assessments));
    } else {
      localStorage.removeItem(ASSESSMENTS_STORAGE_KEY);
    }
  }, [assessments]);

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

  const handleGenerateAssessments = () => {
    setIsGenerating(true);

    if (assessments === null || assessments.cpra.assessments.length === 0) {
      // First time generating or all assessments deleted
      toast(
        successToastParams(
          "2 privacy declarations eligible for assessments in the configured regions.",
          "Generating assessments",
        ),
      );

      // Simulate a delay for generating assessments
      setTimeout(() => {
        setAssessments(generatedAssessments);
        setIsGenerating(false);
      }, 2000);
    } else {
      // Check for missing assessments
      const existingIds = assessments.cpra.assessments.map((a) => a.id);
      const missingAssessments = generatedAssessments.cpra.assessments.filter(
        (a) => !existingIds.includes(a.id),
      );

      setTimeout(() => {
        if (missingAssessments.length > 0) {
          // Add missing assessments
          toast(
            successToastParams(
              `${missingAssessments.length} privacy declaration${missingAssessments.length > 1 ? "s" : ""} eligible for assessments.`,
              "Generating assessments",
            ),
          );
          setAssessments((prev) => {
            if (!prev) return generatedAssessments;
            return {
              ...prev,
              cpra: {
                ...prev.cpra,
                assessments: [...prev.cpra.assessments, ...missingAssessments],
              },
            };
          });
        } else {
          // No changes found
          toast({
            ...DEFAULT_TOAST_PARAMS,
            description:
              "No changes detected that require new or updated assessments.",
            status: "info",
          });
        }
        setIsGenerating(false);
      }, 1500);
    }
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

  const hasAssessments = assessments !== null;

  return (
    <Layout title="Privacy assessments">
      <PageHeader
        heading="Privacy assessments"
        rightContent={
          hasAssessments ? (
            <Button
              type="primary"
              onClick={handleGenerateAssessments}
              loading={isGenerating}
            >
              {isGenerating ? "Re-evaluating..." : "Re-evaluate assessments"}
            </Button>
          ) : undefined
        }
        isSticky
      />

      {!hasAssessments ? (
        <EmptyState
          onGenerate={handleGenerateAssessments}
          isGenerating={isGenerating}
        />
      ) : (
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
                  {template.assessments.map((assessment) => (
                    <Card
                      key={assessment.id}
                      hoverable
                      style={{
                        width: "calc((100% - 48px) / 4)",
                        minWidth: 280,
                        cursor: "pointer",
                        display: "flex",
                        flexDirection: "column",
                        ...(assessment.completeness === 100 && {
                          borderLeft: `4px solid ${palette.FIDESUI_SUCCESS}`,
                        }),
                      }}
                      styles={{
                        body: {
                          display: "flex",
                          flexDirection: "column",
                          flex: 1,
                        },
                      }}
                      onClick={() =>
                        router.push(
                          `${PRIVACY_ASSESSMENTS_ROUTE}/${assessment.id}`,
                        )
                      }
                    >
                      <Flex
                        vertical
                        gap="small"
                        style={{ flex: 1 }}
                        justify="space-between"
                      >
                        <div>
                          <Title
                            level={5}
                            style={{
                              margin: 0,
                              marginBottom: 8,
                            }}
                          >
                            {assessment.name}
                          </Title>
                          <Text
                            type="secondary"
                            style={{
                              fontSize: 12,
                              display: "block",
                              marginBottom: 8,
                            }}
                          >
                            System: {assessment.system}
                          </Text>
                          <Text
                            type="secondary"
                            style={{
                              fontSize: 12,
                              lineHeight: "24px",
                              display: "block",
                              marginBottom: 8,
                            }}
                          >
                            Processing{" "}
                            {assessment.dataCategories.map((category, idx) => (
                              <span key={category}>
                                <Tag
                                  color={CUSTOM_TAG_COLOR.DEFAULT}
                                  style={{
                                    margin: 0,
                                    fontSize: 11,
                                    verticalAlign: "middle",
                                  }}
                                >
                                  {category}
                                </Tag>
                                {idx < assessment.dataCategories.length - 1 && " "}
                              </span>
                            ))}{" "}
                            for{" "}
                            <Tag
                              color={CUSTOM_TAG_COLOR.DEFAULT}
                              style={{
                                margin: 0,
                                fontSize: 11,
                                verticalAlign: "middle",
                              }}
                            >
                              {assessment.dataUse}
                            </Tag>
                          </Text>
                          <div>
                            {getRiskTag(assessment.riskLevel)}
                          </div>
                        </div>
                        <div>
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
                                  <Button type="link" style={{ padding: 0 }}>
                                    Resume
                                  </Button>
                                </Flex>
                              </Flex>
                            </div>
                          )}
                        </div>
                      </Flex>
                    </Card>
                  ))}
                </Flex>
              </div>
            ))}
          </Space>
        </div>
      )}
    </Layout>
  );
};

export default PrivacyAssessmentsPage;
