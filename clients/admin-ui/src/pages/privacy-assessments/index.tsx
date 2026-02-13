import {
  Button,
  Flex,
  Icons,
  Result,
  Space,
  Spin,
  Text,
  Typography,
  useMessage,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  useCreatePrivacyAssessmentMutation,
  useGetPrivacyAssessmentsQuery,
} from "~/features/privacy-assessments";

import { AssessmentCard } from "./AssessmentCard";
import { EmptyState } from "./EmptyState";

const { Title } = Typography;

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
        `Generated assessments for ${result.total_created} privacy declaration(s)`,
      );
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error("Assessment generation failed:", error);
      message.error(
        `Assessment generation failed: ${error instanceof Error ? error.message : "Unknown error"}`,
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
        <Flex align="center" justify="center" className="px-10 py-20">
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
        <div className="px-10 py-6">
          <Space direction="vertical" size="large" className="w-full">
            {Object.entries(groupedAssessments).map(([key, template]) => (
              <div key={key}>
                <Flex
                  justify="space-between"
                  align="flex-end"
                  className="mb-4 border-b border-gray-200 pb-2"
                >
                  <Flex gap="middle" align="center">
                    <div className="flex size-10 items-center justify-center rounded border border-gray-200">
                      <Icons.Document />
                    </div>
                    <div>
                      <Title level={4} className="!m-0">
                        {template.title}
                      </Title>
                      <Text type="secondary" className="text-sm">
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
                          `${PRIVACY_ASSESSMENTS_ROUTE}/${assessment.id}`,
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
