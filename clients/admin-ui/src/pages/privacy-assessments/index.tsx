import { Alert, Button, Flex, Icons, Result, Space, Spin } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_EVALUATE_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  AssessmentGroup,
  AssessmentSettingsModal,
  AssessmentTaskStatusIndicator,
  EmptyState,
  useGetAssessmentTasksQuery,
  useGetAssessmentTemplatesQuery,
  useGetPrivacyAssessmentsQuery,
} from "~/features/privacy-assessments";
import { TaskStatus } from "~/features/privacy-assessments/types";

const PrivacyAssessmentsPage: NextPage = () => {
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  const [showCompletionBanner, setShowCompletionBanner] = useState(false);

  // Fetch assessments from API
  const {
    data: assessmentsData,
    isLoading,
    isError,
    refetch: refetchAssessments,
  } = useGetPrivacyAssessmentsQuery({ page: 1, size: 100 });

  const assessments = useMemo(
    () => assessmentsData?.items ?? [],
    [assessmentsData?.items],
  );

  const [taskPollingInterval, setTaskPollingInterval] = useState(5000);

  const { data: tasksData } = useGetAssessmentTasksQuery(
    { page: 1, size: 10 },
    { pollingInterval: taskPollingInterval },
  );

  const tasks = tasksData?.items ?? [];

  const activeTask =
    tasks.find(
      (t) =>
        t.status === TaskStatus.IN_PROCESSING ||
        t.status === TaskStatus.PENDING,
    ) ?? null;

  const hasActiveTask = activeTask !== null;

  // Most recent non-active task (for popover detail when idle)
  const lastCompletedTask =
    tasks.find(
      (t) => t.status === TaskStatus.COMPLETE || t.status === TaskStatus.ERROR,
    ) ?? null;

  // Track whether a task was active on the previous render to detect completion
  const hadActiveTaskRef = useRef(false);

  // Adjust polling rate and detect task completion
  useEffect(() => {
    setTaskPollingInterval(hasActiveTask ? 5000 : 30000);
    if (hadActiveTaskRef.current && !hasActiveTask) {
      setShowCompletionBanner(true);
    }
    hadActiveTaskRef.current = hasActiveTask;
  }, [hasActiveTask]);

  // Most recent assessment date (for "Last assessment X ago" display)
  const lastAssessmentDate = useMemo(() => {
    const dates = assessments
      .map((a) => (a.updated_at ? new Date(a.updated_at) : null))
      .filter((d): d is Date => d !== null);
    if (dates.length === 0) {
      return null;
    }
    return new Date(Math.max(...dates.map((d) => d.getTime())));
  }, [assessments]);

  // Fetch templates from API
  const { data: templatesData } = useGetAssessmentTemplatesQuery({
    page: 1,
    size: 100,
  });

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

  const handleReloadResults = () => {
    refetchAssessments();
    setShowCompletionBanner(false);
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
          <Space align="center">
            <AssessmentTaskStatusIndicator
              activeTask={activeTask}
              lastCompletedTask={lastCompletedTask}
              lastAssessmentDate={lastAssessmentDate}
              className="mr-2"
            />
            {hasAssessments && (
              <NextLink href={PRIVACY_ASSESSMENTS_EVALUATE_ROUTE} passHref>
                <Button type="primary">Evaluate assessments</Button>
              </NextLink>
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

      {showCompletionBanner && (
        <Alert
          message="New assessment results are available"
          type="success"
          showIcon
          action={
            <Button size="small" onClick={handleReloadResults}>
              Reload results
            </Button>
          }
          closable
          onClose={() => setShowCompletionBanner(false)}
          className="mb-4"
        />
      )}

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
