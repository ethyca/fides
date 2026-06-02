import {
  Avatar,
  Button,
  Card,
  ExitGrid,
  Icons,
  Space,
  SparkleIcon,
  Text,
} from "fidesui";
import { HTMLAttributes, ReactNode, useMemo } from "react";

import { RouterLink } from "~/features/common/nav/RouterLink";
import { nFormatter, pluralize } from "~/features/common/utils";

import { useWebsiteMonitorCounts } from "./useWebsiteMonitorCounts";

interface WebsiteFindingItem {
  key: string;
  label: string;
  count: number;
  icon: ReactNode;
}

interface WebsiteFindingsRowProps extends HTMLAttributes<HTMLDivElement> {
  monitorId: string;
  totalAdditions: number;
  /** Link to the monitor's results view. */
  reviewHref: string;
}

/**
 * Root action-center "Findings" cards for a website monitor — the web-monitor
 * analogue of the datastore ConfidenceRow. Mirrors its ExitGrid + Card layout
 * and quick-action styling, filled in with classified / unclassified /
 * compliance-issue counts.
 */
export const WebsiteFindingsRow = ({
  monitorId,
  totalAdditions,
  reviewHref,
  ...props
}: WebsiteFindingsRowProps) => {
  const { labeled, unlabeled, complianceIssues } = useWebsiteMonitorCounts(
    monitorId,
    totalAdditions,
  );

  const dataSource = useMemo<WebsiteFindingItem[]>(
    () =>
      [
        {
          key: "classified",
          label: "Classified",
          count: labeled,
          icon: <SparkleIcon color="black" />,
        },
        {
          key: "unlabeled",
          label: "Unlabeled",
          count: unlabeled,
          icon: <SparkleIcon color="black" />,
        },
        {
          key: "compliance",
          label: "Compliance issues",
          count: complianceIssues,
          icon: (
            <Icons.WarningAltFilled
              size={14}
              style={{ color: "var(--fidesui-color-error)" }}
            />
          ),
        },
      ].filter((item) => item.count > 0),
    [labeled, unlabeled, complianceIssues],
  );

  return (
    <ExitGrid<WebsiteFindingItem>
      dataSource={dataSource}
      itemKey={(item) => item.key}
      columns={3}
      gutter={4}
      renderItem={(item) => (
        <Card
          size="small"
          styles={{ body: { display: "none" } }}
          title={
            <Space>
              <Avatar size={24} icon={item.icon} />
              <Text type="secondary" className="font-normal">
                {nFormatter(item.count)}{" "}
                {pluralize(item.count, "asset", "assets")}
              </Text>
              <Text>{item.label}</Text>
            </Space>
          }
          actions={[
            <RouterLink href={reviewHref} key="action">
              {item.key === "classified" ? (
                <Button
                  type="text"
                  size="small"
                  icon={<Icons.CheckmarkOutline />}
                  aria-label="Approve classified assets"
                >
                  Approve
                </Button>
              ) : (
                <Button
                  type="text"
                  size="small"
                  icon={<Icons.ListBoxes />}
                  aria-label={`Review ${item.label} assets`}
                >
                  Review
                </Button>
              )}
            </RouterLink>,
          ]}
        />
      )}
      {...props}
    />
  );
};

export default WebsiteFindingsRow;
