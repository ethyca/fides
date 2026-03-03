import { Button, Flex, Icons, Result, Space, Spin } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_EVALUATE_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  AssessmentGroup,
  AssessmentSettingsModal,
  AssessmentTaskStatusIndicator,
  EmptyState,
  useGetAssessmentTaskQuery,
  useGetAssessmentTasksQuery,
  useGetAssessmentTemplatesQuery,
  useGetPrivacyAssessmentsQuery,
} from "~/features/privacy-assessments";
import { TaskStatus } from "~/features/privacy-assessments/types";
import { useGetSystemsQuery } from "~/features/system/system.slice";

const ACTIVE_POLL_INTERVAL = 5000;

const PrivacyAssessmentsPage: NextPage = () => {
  const router = useRouter();
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);

  // Track a specific task by ID (set from router query on navigation from evaluate page)
  const [trackedTaskId, setTrackedTaskId] = useState<string | null>(
    () => (router.query.taskId as string) ?? null,
  );

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

  // When a taskId arrives via router query (navigated from evaluate page), start tracking it
  useEffect(() => {
    const queryTaskId = router.query.taskId as string | undefined;
    if (queryTaskId && queryTaskId !== trackedTaskId) {
      setTrackedTaskId(queryTaskId);
      // Clean up the query param without a navigation
      router.replace({ pathname: router.pathname }, undefined, {
        shallow: true,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router.query.taskId]);

  const isTrackedTaskActive = trackedTaskId !== null;

  // Poll the single-task endpoint while we have a tracked task ID
  const { data: trackedTask } = useGetAssessmentTaskQuery(trackedTaskId ?? "", {
    skip: !isTrackedTaskActive,
    pollingInterval: ACTIVE_POLL_INTERVAL,
  });

  const isTrackedTaskFinished =
    trackedTask?.status === TaskStatus.COMPLETE ||
    trackedTask?.status === TaskStatus.ERROR;

  // Stop tracking once the task reaches a terminal state
  useEffect(() => {
    if (isTrackedTaskFinished) {
      setTrackedTaskId(null);
    }
  }, [isTrackedTaskFinished]);

  // Fall back to list query when not tracking a specific task (for "last completed" display)
  const { data: tasksData } = useGetAssessmentTasksQuery(
    { page: 1, size: 10 },
    { skip: isTrackedTaskActive },
  );

  const activeTask = useMemo(() => {
    if (isTrackedTaskActive && trackedTask) {
      const isActive =
        trackedTask.status === TaskStatus.IN_PROCESSING ||
        trackedTask.status === TaskStatus.PENDING;
      return isActive ? trackedTask : null;
    }
    return (
      (tasksData?.items ?? []).find(
        (t) =>
          t.status === TaskStatus.IN_PROCESSING ||
          t.status === TaskStatus.PENDING,
      ) ?? null
    );
  }, [isTrackedTaskActive, trackedTask, tasksData]);

  const lastCompletedTask = useMemo(() => {
    if (isTrackedTaskActive && trackedTask && isTrackedTaskFinished) {
      return trackedTask;
    }
    return (
      (tasksData?.items ?? []).find(
        (t) =>
          t.status === TaskStatus.COMPLETE || t.status === TaskStatus.ERROR,
      ) ?? null
    );
  }, [isTrackedTaskActive, trackedTask, isTrackedTaskFinished, tasksData]);

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

  const templates = useMemo(
    () => templatesData?.items ?? [],
    [templatesData?.items],
  );

  // Build label maps for the task status popover
  const templateNamesMap = useMemo(
    () =>
      Object.fromEntries(
        templates.flatMap((t) => {
          const { name } = t;
          const entries: [string, string][] = [[t.key, name]];
          if (t.assessment_type) {
            entries.push([t.assessment_type, name]);
          }
          return entries;
        }),
      ),
    [templates],
  );

  const { data: systemsData } = useGetSystemsQuery({
    page: 1,
    size: 1000,
  });

  const systemNamesMap = useMemo(
    () =>
      Object.fromEntries(
        (systemsData?.items ?? [])
          .filter((s) => s.name !== null && s.name !== undefined)
          .map((s) => [s.fides_key, s.name as string]),
      ),
    [systemsData],
  );

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
              systemNamesMap={systemNamesMap}
              templateNamesMap={templateNamesMap}
              onTaskFinish={handleReloadResults}
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
