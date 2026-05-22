import {
  Button,
  Icons,
  Layout as AntLayout,
  Result,
  Space,
  Spin,
} from "fidesui";
import type { NextPage } from "next";
import { useMemo, useState } from "react";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import {
  AssessmentFilterKey,
  AssessmentFilters,
  AssessmentGroup,
  AssessmentGroupResponse,
  assessmentMatchesFilter,
  AssessmentSettingsModal,
  AssessmentStatsBar,
  AssessmentTaskStatusIndicator,
  EmptyState,
  GenerateAssessmentsModal,
  useGetPrivacyAssessmentsQuery,
  ViewMode,
} from "~/features/privacy-assessments";

function filterGroups(
  groups: AssessmentGroupResponse[],
  filter: AssessmentFilterKey,
  search: string,
): AssessmentGroupResponse[] {
  const query = search.trim().toLowerCase();
  return groups
    .map((group) => {
      let assessments = (group.assessments ?? []).filter((a) =>
        assessmentMatchesFilter(a, filter),
      );
      if (query) {
        assessments = assessments.filter(
          (a) =>
            (a.name ?? "").toLowerCase().includes(query) ||
            (a.system_name ?? "").toLowerCase().includes(query) ||
            (a.template_name ?? "").toLowerCase().includes(query),
        );
      }
      return { ...group, assessments };
    })
    .filter((group) => (group.assessments ?? []).length > 0);
}

const PrivacyAssessmentsPage: NextPage = () => {
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  const [generateModalOpen, setGenerateModalOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState<AssessmentFilterKey>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");

  const {
    data: assessmentsData,
    isLoading,
    isError,
    refetch: refetchAssessments,
  } = useGetPrivacyAssessmentsQuery();

  const groups = assessmentsData?.items ?? [];
  const hasAssessments = groups.length > 0;

  const filteredGroups = useMemo(
    () => filterGroups(groups, activeFilter, searchQuery),
    [groups, activeFilter, searchQuery],
  );

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
    <Layout title="Privacy assessments" padded={false}>
      <AntLayout>
        <AntLayout.Content className="overflow-auto px-10 py-6">
          <PageHeader
            heading="Privacy assessments"
            description="A running record of DPIAs, risk assessments, and transfer evaluations — grouped by the system they evaluate. The Fides agent drafts; you review and sign."
            size="large"
            rightContent={
              <Space align="center">
                <AssessmentTaskStatusIndicator
                  onTaskFinish={refetchAssessments}
                  className="mr-2"
                />
                <Button
                  aria-label="Assessment settings"
                  icon={<Icons.Settings />}
                  onClick={() => setSettingsModalOpen(true)}
                  data-testid="btn-assessment-settings"
                />
                {hasAssessments && (
                  <Button
                    type="primary"
                    onClick={() => setGenerateModalOpen(true)}
                  >
                    Generate assessments
                  </Button>
                )}
              </Space>
            }
            isSticky={false}
          />

          {!hasAssessments ? (
            <EmptyState onRunAssessment={() => setGenerateModalOpen(true)} />
          ) : (
            <div className="py-6">
              <AssessmentStatsBar groups={groups} />
              <div className="mt-10">
                <AssessmentFilters
                  groups={groups}
                  activeFilter={activeFilter}
                  onFilterChange={setActiveFilter}
                  searchQuery={searchQuery}
                  onSearchChange={setSearchQuery}
                  viewMode={viewMode}
                  onViewModeChange={setViewMode}
                />
              </div>
              <Space
                orientation="vertical"
                size="large"
                className="mt-2 w-full"
              >
                {filteredGroups.map((group, i) => (
                  <AssessmentGroup
                    key={group.data_use ?? `uncategorized-${i}`}
                    index={i}
                    dataUseName={group.data_use_name}
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
        </AntLayout.Content>
      </AntLayout>
    </Layout>
  );
};

export default PrivacyAssessmentsPage;
