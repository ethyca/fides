import { Tabs } from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

import { RequestLogTable } from "./RequestLogTable";
import { useRequestLogFilterContext } from "./hooks/useRequestLogFilters";
import { ViolationDetailDrawer } from "./ViolationDetailDrawer";
import { FindingsTable } from "./FindingsTable";
import type { PolicyViolationAggregate, PolicyViolationLog } from "./types";

type TableTab = "summary" | "log";

export const AccessControlTableTabs = () => {
  const router = useRouter();
  const { applyFacets } = useRequestLogFilterContext();

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
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </>
  );
};
