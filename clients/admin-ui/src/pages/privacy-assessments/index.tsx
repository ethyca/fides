import {
  Button,
  Flex,
  Icons,
  Result,
  Space,
  Spin,
  Text,
  Typography,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import {
  PRIVACY_ASSESSMENTS_EVALUATE_ROUTE,
  PRIVACY_ASSESSMENTS_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  useGetAssessmentTemplatesQuery,
  useGetPrivacyAssessmentsQuery,
} from "~/features/privacy-assessments";

import { AssessmentCard } from "./AssessmentCard";
import { EmptyState } from "./EmptyState";

const { Title } = Typography;

const PrivacyAssessmentsPage: NextPage = () => {
  const { flags } = useFeatures();
  const router = useRouter();

  // Fetch assessments from API
  const {
    data: assessmentsData,
    isLoading,
    isError,
  } = useGetPrivacyAssessmentsQuery();

  // Fetch templates from API
  const { data: templatesData } = useGetAssessmentTemplatesQuery();

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

  const assessments = assessmentsData?.items ?? [];
  const templates = templatesData?.items ?? [];
  const hasAssessments = assessments.length > 0;

  // Group assessments by template_id dynamically
  const groupedAssessments = templates
    .map((template) => ({
      templateId: template.id,
      key: template.key,
      title: template.name,
      description: template.description,
      assessments: assessments.filter(
        (a) => a.template_id === template.id || a.template_id === template.key,
      ),
    }))
    .filter((group) => group.assessments.length > 0);

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
              onClick={() => router.push(PRIVACY_ASSESSMENTS_EVALUATE_ROUTE)}
            >
              Re-evaluate assessments
            </Button>
          ) : undefined
        }
        isSticky
      />

      {!hasAssessments ? (
        <EmptyState />
      ) : (
        <div className="px-10 py-6">
          <Space direction="vertical" size="large" className="w-full">
            {groupedAssessments.map((template) => (
              <div key={template.key}>
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
