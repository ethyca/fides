import { Tabs } from "fidesui";
import { parseAsString, parseAsStringLiteral, useQueryState } from "nuqs";
import { useCallback, useMemo } from "react";

import { RequestLogTable } from "./RequestLogTable";
import { SummaryCards } from "./SummaryCards";
import type { PolicyViolationLog } from "./types";
import { ViolationDetailDrawer } from "./ViolationDetailDrawer";

type TableTab = "summary" | "log";

export const AccessControlTableTabs = () => {

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
        children: <SummaryCards />,
      },
      {
        key: "log",
        label: "Log",
        children: <RequestLogTable onRowClick={handleLogRowClick} />,
      },
    ],
    [handleLogRowClick],
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
