import { Text } from "fidesui";

import { nFormatter } from "~/features/common/utils";

import { useWebsiteMonitorCounts } from "./useWebsiteMonitorCounts";

interface WebsiteMonitorSubheaderProps {
  monitorId: string;
  /** Total ADDITION-status assets for the monitor (from the aggregate record). */
  totalAdditions: number;
}

/**
 * Root action-center subheader for website monitors: a plain comma-separated
 * string of classified (assets assigned to a system), unclassified
 * (Uncategorized), and compliance-issue counts.
 */
const WebsiteMonitorSubheader = ({
  monitorId,
  totalAdditions,
}: WebsiteMonitorSubheaderProps) => {
  const { labeled, unlabeled, complianceIssues } = useWebsiteMonitorCounts(
    monitorId,
    totalAdditions,
  );

  const summary = [
    `${nFormatter(labeled)} classified`,
    `${nFormatter(unlabeled)} unlabeled`,
    `${nFormatter(complianceIssues)} compliance ${
      complianceIssues === 1 ? "issue" : "issues"
    }`,
  ].join(", ");

  return (
    <Text type="secondary" data-testid="website-subheader">
      {summary}
    </Text>
  );
};

export default WebsiteMonitorSubheader;
