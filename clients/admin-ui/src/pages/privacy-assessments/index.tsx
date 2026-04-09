import { Button, Icons, Result, Space, Spin } from "fidesui";
import type { NextPage } from "next";
import { useMemo, useState } from "react";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import {
  AssessmentGroup,
  AssessmentSettingsModal,
  AssessmentTaskStatusIndicator,
  EmptyState,
  GenerateAssessmentsModal,
  useGetPrivacyAssessmentsQuery,
  useGetProcessingActivitiesQuery,
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

  const assessments = useMemo(
    () => assessmentsData?.items ?? [],
    [assessmentsData],
  );

  const { data: processingActivitiesData } = useGetProcessingActivitiesQuery();

  const processingActivities = useMemo(
    () => processingActivitiesData?.items ?? [],
    [processingActivitiesData],
  );

  const hasAssessments = assessments.length > 0;

  const groupedAssessments = useMemo(() => {
    // Sort: null data_use ("Uncategorized") goes last
    const sorted = [...processingActivities].sort((a, b) => {
      if (a.data_use === null && b.data_use === null) {
        return 0;
      }
      if (a.data_use === null) {
        return 1;
      }
      if (b.data_use === null) {
        return -1;
      }
      return (a.data_use_name ?? "").localeCompare(b.data_use_name ?? "");
    });
    return sorted
      .map((activity) => ({
        dataUse: activity.data_use,
        dataUseName: activity.data_use_name,
        systemCount: activity.system_count,
        assessments: assessments.filter(
          (a) => (a.data_use ?? null) === activity.data_use,
        ),
      }))
      .filter((group) => group.assessments.length > 0);
  }, [processingActivities, assessments]);

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
            {groupedAssessments.map((group) => (
              <AssessmentGroup
                key={group.dataUse ?? "uncategorized"}
                dataUseName={group.dataUseName}
                systemCount={group.systemCount}
                assessments={group.assessments}
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
