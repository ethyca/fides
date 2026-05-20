import { Flex, Input, Segmented, Text } from "fidesui";

import styles from "./AssessmentFilters.module.scss";
import { AssessmentFilterKey, AssessmentGroupResponse } from "./types";
import { assessmentMatchesFilter } from "./utils";

export type ViewMode = "grid" | "list";

interface AssessmentFiltersProps {
  groups: AssessmentGroupResponse[];
  activeFilter: AssessmentFilterKey;
  onFilterChange: (filter: AssessmentFilterKey) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
}

export const AssessmentFilters = ({
  groups,
  activeFilter,
  onFilterChange,
  searchQuery,
  onSearchChange,
  viewMode,
  onViewModeChange,
}: AssessmentFiltersProps) => {
  const allAssessments = groups.flatMap((g) => g.assessments ?? []);

  const filterItems: { key: AssessmentFilterKey; label: string }[] = [
    { key: "all", label: "All" },
    { key: "needs_input", label: "Needs input" },
    { key: "agent_drafting", label: "Agent drafting" },
    { key: "slack", label: "Slack" },
    { key: "high_risk", label: "High risk" },
    { key: "signed", label: "Signed" },
  ];

  // Route every chip count through the same predicate the page uses to
  // actually filter, so the numbers can never disagree with what's on screen.
  const counts = Object.fromEntries(
    filterItems.map((item) => [
      item.key,
      allAssessments.filter((a) => assessmentMatchesFilter(a, item.key)).length,
    ]),
  ) as Record<AssessmentFilterKey, number>;

  return (
    <Flex justify="space-between" align="center" className={styles.container}>
      <Segmented
        value={activeFilter}
        onChange={(val) => onFilterChange(val as AssessmentFilterKey)}
        options={filterItems.map((item) => ({
          value: item.key,
          label: (
            <Flex gap={8} align="baseline">
              <span>{item.label}</span>
              <Text type="secondary" size="sm">
                {String(counts[item.key as AssessmentFilterKey]).padStart(
                  2,
                  "0",
                )}
              </Text>
            </Flex>
          ),
        }))}
      />
      <Flex gap={12} align="center">
        <Input
          placeholder="Find an assessment"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          allowClear
          className={styles.searchInput}
        />
        <Segmented
          value={viewMode}
          onChange={(val) => onViewModeChange(val as ViewMode)}
          options={[
            { value: "grid", label: "GRID" },
            { value: "list", label: "LIST" },
          ]}
        />
      </Flex>
    </Flex>
  );
};
