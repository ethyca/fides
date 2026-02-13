import { Button, Flex, Result, Space, Spin } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_EVALUATE_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  useGetAssessmentTemplatesQuery,
  useGetPrivacyAssessmentsQuery,
} from "~/features/privacy-assessments";

import { AssessmentGroup } from "./AssessmentGroup";
import { EmptyState } from "./EmptyState";

const PrivacyAssessmentsPage: NextPage = () => {
  const router = useRouter();

  // Fetch assessments from API
  const {
    data: assessmentsData,
    isLoading,
    isError,
  } = useGetPrivacyAssessmentsQuery();

  // Fetch templates from API
  const { data: templatesData } = useGetAssessmentTemplatesQuery();

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
              <AssessmentGroup
                key={template.key}
                templateId={template.templateId}
                title={template.title}
                assessments={template.assessments}
              />
            ))}
          </Space>
        </div>
      )}
    </Layout>
  );
};

export default PrivacyAssessmentsPage;
