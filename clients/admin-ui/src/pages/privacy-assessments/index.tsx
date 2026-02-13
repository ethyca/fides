import { FileTextOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  CUSTOM_TAG_COLOR,
  Flex,
  PlusOutlined,
  Result,
  Space,
  Spin,
  Tag,
  Typography,
  useMessage,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  PrivacyAssessmentResponse,
  useCreatePrivacyAssessmentMutation,
  useGetPrivacyAssessmentsQuery,
} from "~/features/privacy-assessments";

const { Title, Text } = Typography;

// Map risk level from API format to UI format
const mapRiskLevel = (riskLevel: string): "High" | "Med" | "Low" => {
  switch (riskLevel) {
    case "high":
      return "High";
    case "medium":
      return "Med";
    case "low":
    default:
      return "Low";
  }
};

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

const AssessmentCard = ({
  assessment,
  onClick,
}: {
  assessment: PrivacyAssessmentResponse;
  onClick: () => void;
}) => {
  const riskLevel = mapRiskLevel(assessment.risk_level);

  const getStatusText = () => {
    if (assessment.status === "completed") {
      return `Completed`;
    }
    if (assessment.status === "outdated") {
      return "Out of date";
    }
    return "In progress";
  };

  const getStatusColor = () => {
    if (assessment.status === "completed") {
      return palette.FIDESUI_SUCCESS;
    }
    if (assessment.status === "outdated") {
      return palette.FIDESUI_ERROR;
    }
    return undefined;
  };

  const getRiskTag = () => {
    const colors: Record<string, CUSTOM_TAG_COLOR> = {
      High: CUSTOM_TAG_COLOR.ERROR,
      Med: CUSTOM_TAG_COLOR.WARNING,
      Low: CUSTOM_TAG_COLOR.DEFAULT,
    };
    return (
      <div style={{ display: "inline-block" }}>
        <Tag color={colors[riskLevel] ?? CUSTOM_TAG_COLOR.DEFAULT}>
          {riskLevel} risk
        </Tag>
      </div>
    );
  };

  return (
    <Card
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
      onClick={onClick}
    >
      <Flex vertical gap="small" style={{ flex: 1 }} justify="space-between">
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
            System: {assessment.system_name}
          </Text>
          {assessment.data_categories.length > 0 && (
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
              {assessment.data_categories.map(
                (category: string, idx: number) => (
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
                    {idx < assessment.data_categories.length - 1 && " "}
                  </span>
                )
              )}{" "}
              for{" "}
              <Tag
                color={CUSTOM_TAG_COLOR.DEFAULT}
                style={{
                  margin: 0,
                  fontSize: 11,
                  verticalAlign: "middle",
                }}
              >
                {assessment.data_use_name}
              </Tag>
            </Text>
          )}
          <div>{getRiskTag()}</div>
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
                    {getStatusText()}
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
                  <Text
                    style={{
                      fontSize: 11,
                      color: getStatusColor(),
                    }}
                  >
                    {getStatusText()}
                  </Text>
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
  );
};

const PrivacyAssessmentsPage: NextPage = () => {
  const { flags } = useFeatures();
  const router = useRouter();
  const message = useMessage();

  // Fetch assessments from API
  const {
    data: assessmentsData,
    isLoading,
    isError,
  } = useGetPrivacyAssessmentsQuery();

  const [createPrivacyAssessment, { isLoading: isGenerating }] =
    useCreatePrivacyAssessmentMutation();

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

  const handleGenerateAssessments = async () => {
    try {
      message.info("Analyzing privacy declarations...");

      const result = await createPrivacyAssessment({
        assessment_type: "cpra",
        use_llm: true,
      }).unwrap();

      message.success(
        `Generated assessments for ${result.total_created} privacy declaration(s)`
      );
    } catch (error) {
      console.error("Assessment generation failed:", error);
      message.error(
        `Assessment generation failed: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    }
  };

  const assessments = assessmentsData?.items ?? [];
  const hasAssessments = assessments.length > 0;

  // Group assessments by template (for now, all CPRA)
  const groupedAssessments = {
    cpra: {
      templateId: "CPRA-RA-2024",
      title: "CPRA Risk Assessment",
      assessments,
    },
  };

  if (isLoading) {
    return (
      <Layout title="Privacy assessments">
        <PageHeader heading="Privacy assessments" isSticky />
        <Flex
          align="center"
          justify="center"
          style={{ padding: "80px 40px" }}
        >
          <Spin size="large" />
        </Flex>
      </Layout>
    );
  }

  if (isError) {
    return (
      <Layout title="Privacy assessments">
        <PageHeader heading="Privacy assessments" isSticky />
        <Result
          status="error"
          title="Failed to load assessments"
          subTitle="There was an error loading your privacy assessments. Please try again."
          extra={
            <Button type="primary" onClick={() => window.location.reload()}>
              Retry
            </Button>
          }
        />
      </Layout>
    );
  }

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
            {Object.entries(groupedAssessments).map(([key, template]) => (
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
                    <AssessmentCard
                      key={assessment.id}
                      assessment={assessment}
                      onClick={() =>
                        router.push(
                          `${PRIVACY_ASSESSMENTS_ROUTE}/${assessment.id}`
                        )
                      }
                    />
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
