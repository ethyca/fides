import { Tabs } from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

import { RequestLogTable } from "./request-log/RequestLogTable";
import { useRequestLogFilterContext } from "./request-log/useRequestLogFilters";
import { ViolationDetailDrawer } from "./request-log/ViolationDetailDrawer";
import { FindingsTable } from "./summary/FindingsTable";
import type { PolicyViolationAggregate, PolicyViolationLog } from "./types";

type TableTab = "summary" | "log";

export const AccessControlTableTabs = () => {
  const router = useRouter();
  const { applyFacets, filters } = useRequestLogFilterContext();

  const [activeTab, setActiveTab] = useState<TableTab>(() => {
    return router.query.tab === "log" ? "log" : "summary";
  });

  const [selectedViolationId, setSelectedViolationId] = useState<string | null>(
    null,
  );
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    if (router.query.tab === "log") {
      setActiveTab("log");
    }
  }, [router.query.tab]);

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
    [applyFacets],
  );

  const handleLogRowClick = useCallback((record: PolicyViolationLog) => {
    setSelectedViolationId(record.id);
    setDrawerOpen(true);
  }, []);

  const items = useMemo(
    () => [
      {
        key: "summary",
        label: "Summary",
        children: (
          <FindingsTable
            onRowClick={handleSummaryRowClick}
            startDate={filters.start_date}
            endDate={filters.end_date}
          />
        ),
      },
      {
        key: "log",
        label: "Log",
        children: <RequestLogTable onRowClick={handleLogRowClick} />,
      },
    ],
    [
      handleSummaryRowClick,
      handleLogRowClick,
      filters.start_date,
      filters.end_date,
    ],
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
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </>
  );
};
