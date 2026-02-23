import { Button, Flex, Icons, Result, Space, Spin, Tooltip } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useState } from "react";

import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_EVALUATE_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  AssessmentGroup,
  AssessmentSettingsModal,
  EmptyState,
  useGetAssessmentTemplatesQuery,
  useGetPrivacyAssessmentsQuery,
} from "~/features/privacy-assessments";

const PrivacyAssessmentsPage: NextPage = () => {
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);

  // Fetch assessments from API
  const {
    data: assessmentsData,
    isLoading,
    isError,
  } = useGetPrivacyAssessmentsQuery({ page: 1, size: 100 });

  // Fetch templates from API
  const { data: templatesData } = useGetAssessmentTemplatesQuery({
    page: 1,
    size: 100,
  });

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
          <Space>
            {hasAssessments && (
              <NextLink href={PRIVACY_ASSESSMENTS_EVALUATE_ROUTE} passHref>
                <Button type="primary">Evaluate assessments</Button>
              </NextLink>
            )}
            <Tooltip title="Assessment settings">
              <Button
                aria-label="Assessment settings"
                icon={<Icons.Settings />}
                onClick={() => setSettingsModalOpen(true)}
                data-testid="btn-assessment-settings"
              />
            </Tooltip>
          </Space>
        }
        isSticky
      />

      {!hasAssessments ? (
        <EmptyState />
      ) : (
        <div className="py-6">
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

      <AssessmentSettingsModal
        open={settingsModalOpen}
        onClose={() => setSettingsModalOpen(false)}
      />
    </Layout>
  );
};

export default PrivacyAssessmentsPage;
