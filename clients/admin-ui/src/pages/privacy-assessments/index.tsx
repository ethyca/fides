import { Button, Icons, Result, Space, Spin } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import {
  AssessmentGroup,
  AssessmentSettingsModal,
  AssessmentStatus,
  AssessmentTaskStatusIndicator,
  EmptyState,
  GenerateAssessmentsModal,
  RiskLevel,
  useGetPrivacyAssessmentsQuery,
} from "~/features/privacy-assessments";

const VALID_STATUSES = new Set<string>(Object.values(AssessmentStatus));
const VALID_RISK_LEVELS = new Set<string>(Object.values(RiskLevel));

function readQueryParam(
  value: string | string[] | undefined,
): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

const PrivacyAssessmentsPage: NextPage = () => {
  const router = useRouter();
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  const [generateModalOpen, setGenerateModalOpen] = useState(false);

  const statusParam = readQueryParam(router.query.status);
  const statusFilter =
    statusParam && VALID_STATUSES.has(statusParam)
      ? (statusParam as AssessmentStatus)
      : undefined;

  const riskLevelParam = readQueryParam(router.query.risk_level);
  const riskLevelFilter =
    riskLevelParam && VALID_RISK_LEVELS.has(riskLevelParam)
      ? (riskLevelParam as RiskLevel)
      : undefined;

  const {
    data: assessmentsData,
    isLoading,
    isError,
    refetch: refetchAssessments,
  } = useGetPrivacyAssessmentsQuery(
    statusFilter ? { status: statusFilter } : undefined,
  );

  const groups = useMemo(() => {
    const all = assessmentsData?.items ?? [];
    if (!riskLevelFilter) {
      return all;
    }
    return all
      .map((group) => ({
        ...group,
        assessments: group.assessments?.filter(
          (a) => a.risk_level === riskLevelFilter,
        ),
      }))
      .filter((group) => (group.assessments?.length ?? 0) > 0);
  }, [assessmentsData?.items, riskLevelFilter]);

  const hasAssessments = groups.length > 0;

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
          <Space orientation="vertical" size="large" className="w-full">
            {groups.map((group, i) => (
              <AssessmentGroup
                key={group.data_use ?? `uncategorized-${i}`}
                dataUseName={group.data_use_name}
                systemCount={group.system_count}
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
