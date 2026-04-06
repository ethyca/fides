import { Button, Icons, Result, Space, Spin } from "fidesui";
import type { NextPage } from "next";
import { useState } from "react";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import {
  AssessmentGroup,
  AssessmentSettingsModal,
  AssessmentTaskStatusIndicator,
  EmptyState,
  GenerateAssessmentsModal,
  useGetAssessmentTemplatesQuery,
  useGetPrivacyAssessmentsQuery,
} from "~/features/privacy-assessments";

const PrivacyAssessmentsPage: NextPage = () => {
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  const [generateModalOpen, setGenerateModalOpen] = useState(false);

  const {
    data: assessmentsData,
    isLoading,
    isError,
    refetch: refetchAssessments,
  } = useGetPrivacyAssessmentsQuery({ page: 1, size: 100 });

  const assessments = assessmentsData?.items ?? [];

  const { data: templatesData } = useGetAssessmentTemplatesQuery({
    page: 1,
    size: 100,
  });

  const templates = templatesData?.items ?? [];

  const hasAssessments = assessments.length > 0;

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
        <Spin size="large" />
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
          <Space align="center">
            <AssessmentTaskStatusIndicator
              onTaskFinish={refetchAssessments}
              className="mr-2"
            />
            {hasAssessments && (
              <Button type="primary" onClick={() => setGenerateModalOpen(true)}>
                Generate assessments
              </Button>
            )}
            <Button
              aria-label="Assessment settings"
              icon={<Icons.Settings />}
              onClick={() => setSettingsModalOpen(true)}
              data-testid="btn-assessment-settings"
            />
          </Space>
        }
        isSticky
      />

      {!hasAssessments ? (
        <EmptyState onRunAssessment={() => setGenerateModalOpen(true)} />
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

      <GenerateAssessmentsModal
        open={generateModalOpen}
        onClose={() => setGenerateModalOpen(false)}
      />

      <AssessmentSettingsModal
        open={settingsModalOpen}
        onClose={() => setSettingsModalOpen(false)}
      />
    </Layout>
  );
};

export default PrivacyAssessmentsPage;
