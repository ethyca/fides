import { Tabs } from "fidesui";
import { parseAsString, parseAsStringLiteral, useQueryState } from "nuqs";
import { useCallback, useMemo } from "react";

import { RequestLogTable } from "./RequestLogTable";
import { useRequestLogFilterContext } from "./hooks/useRequestLogFilters";
import { ViolationDetailDrawer } from "./ViolationDetailDrawer";
import { FindingsTable } from "./FindingsTable";
import type { PolicyViolationAggregate, PolicyViolationLog } from "./types";

type TableTab = "summary" | "log";

export const AccessControlTableTabs = () => {
  const { applyFacets } = useRequestLogFilterContext();

  const [activeTab, setActiveTab] = useQueryState(
    "tab",
    parseAsStringLiteral(["summary", "log"] as const)
      .withDefault("summary")
      .withOptions({ history: "push" }),
  );

  const [selectedViolationId, setSelectedViolationId] = useQueryState(
    "violationId",
    parseAsString.withOptions({ history: "push" }),
  );

  const handleSummaryRowClick = useCallback(
    (record: PolicyViolationAggregate) => {
      const facets: Record<string, string> = {};
      if (record.policy) {
        facets.policy = record.policy;
      }
      if (record.control) {
        facets.control = record.control;
      }
      applyFacets(facets);
      setActiveTab("log");
    },
    [applyFacets, setActiveTab],
  );

  const handleLogRowClick = useCallback(
    (record: PolicyViolationLog) => {
      setSelectedViolationId(record.id);
    },
    [setSelectedViolationId],
  );

  const items = useMemo(
    () => [
      {
        key: "summary",
        label: "Summary",
        children: <FindingsTable onRowClick={handleSummaryRowClick} />,
      },
      {
        key: "log",
        label: "Log",
        children: <RequestLogTable onRowClick={handleLogRowClick} />,
      },
    ],
    [handleSummaryRowClick, handleLogRowClick],
  );

  return (
    <>
      <Tabs
        activeKey={activeTab}
        onChange={(key) => setActiveTab(key as TableTab)}
        items={items}
      />
      <ViolationDetailDrawer
        violationId={selectedViolationId}
        open={!!selectedViolationId}
        onClose={() => setSelectedViolationId(null)}
      />
    </>
  );
};
