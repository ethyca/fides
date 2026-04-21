import { Button, Divider, Flex, Icons, SparkleIcon, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import type { NextPage } from "next";
import { useCallback, useState } from "react";

import {
  MOCK_GAP_CARDS,
  MOCK_UNRESOLVED_IDENTITIES,
  MOCK_VIOLATION_CARDS,
} from "~/features/access-control/mockData";
import PolicyDrillDown from "~/features/access-control-v2/PolicyDrillDown";
import PostureBar from "~/features/access-control-v2/PostureBar";
import ViolationsTable from "~/features/access-control-v2/ViolationsTable";
import type { TableTab } from "~/features/access-control-v2/ViolationsTable";
import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";

const AccessControlV2Page: NextPage = () => {
  const [selectedPolicy, setSelectedPolicy] = useState<string | null>(null);
  const [tableTab, setTableTab] = useState<TableTab | undefined>(undefined);
  const [bannerDismissed, setBannerDismissed] = useState(false);

  const violationCount = MOCK_VIOLATION_CARDS.length;
  const gapCount = MOCK_GAP_CARDS.length;
  const unresolvedCount = MOCK_UNRESOLVED_IDENTITIES.length;

  // Mock compliant queries — known consumers accessing data within policy
  const compliantQueries = 100;
  const consumerCount = 7;
  const policyCount = 12;

  // Access health: ratio of compliant to total observed access
  const totalFindings = violationCount + gapCount + unresolvedCount;
  const accessHealthScore = Math.max(
    0,
    Math.round((compliantQueries / (compliantQueries + totalFindings)) * 100),
  );
  const violationRate = Math.round(
    (violationCount / (compliantQueries + violationCount)) * 100,
  );
  const totalQueries = 3554;
  const systemsMonitored = 8;

  const topInferredPurposes = [
    { name: "Campaign targeting", queryCount: 1061 },
    { name: "Analytics", queryCount: 892 },
    { name: "Model training", queryCount: 734 },
    { name: "Financial reporting", queryCount: 588 },
    { name: "Ticket resolution", queryCount: 279 },
  ];

  const handleReviewUnknown = useCallback(() => {
    setTableTab("unknown");
    setBannerDismissed(true);
  }, []);

  // ─── Drill-down view ─────────────────────────────────────────────────
  if (selectedPolicy) {
    return (
      <FixedLayout title={selectedPolicy}>
        <PageHeader
          breadcrumbItems={[
            {
              title: "Data access governance",
              href: "/data-discovery/access-control-v2",
              onClick: (e) => {
                e.preventDefault();
                setSelectedPolicy(null);
              },
            },
            { title: selectedPolicy },
          ]}
        />
        <PolicyDrillDown
          policyName={selectedPolicy}
          onBack={() => setSelectedPolicy(null)}
        />
      </FixedLayout>
    );
  }

  // ─── Main view ───────────────────────────────────────────────────────
  return (
    <FixedLayout title="Data access governance">
      <PageHeader heading="Data access governance" />

      <Flex vertical gap={24}>
        {/* Unknown identities banner */}
        {unresolvedCount > 0 && !bannerDismissed && (
          <div
            className="rounded-lg px-5 py-4"
            style={{ backgroundColor: palette.FIDESUI_BG_DEFAULT }}
          >
            <Flex gap={12} align="flex-start" className="min-w-0">
              <SparkleIcon size={16} className="mt-1 shrink-0" />
              <Flex vertical gap={6} className="min-w-0 flex-1">
                <Text className="text-sm leading-relaxed">
                  <strong>Unknown identities accessing data</strong> —
                  we&apos;ve found service accounts and users in your query logs
                  that aren&apos;t registered as consumers. Until they&apos;re
                  resolved, some findings may be incomplete.
                </Text>
                <Flex align="center" gap={6}>
                  <div
                    className="size-2 shrink-0 rounded-full"
                    style={{ backgroundColor: palette.FIDESUI_WARNING }}
                  />
                  <Text className="min-w-0 flex-1 text-xs">
                    {unresolvedCount} unknown{" "}
                    {unresolvedCount === 1 ? "identity" : "identities"}{" "}
                    discovered
                  </Text>
                  <Button
                    type="text"
                    size="small"
                    className="!px-0 !text-xs"
                    style={{ color: palette.FIDESUI_MINOS }}
                    onClick={handleReviewUnknown}
                  >
                    Review
                  </Button>
                  <span
                    role="button"
                    aria-label="Dismiss"
                    tabIndex={0}
                    className="shrink-0 cursor-pointer"
                    onClick={() => setBannerDismissed(true)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ")
                        setBannerDismissed(true);
                    }}
                  >
                    <Icons.Close
                      size={12}
                      style={{ color: palette.FIDESUI_NEUTRAL_500 }}
                    />
                  </span>
                </Flex>
              </Flex>
            </Flex>
          </div>
        )}

        {/* Dashboard */}
        <PostureBar
          accessHealthScore={accessHealthScore}
          compliantQueries={compliantQueries}
          violationCount={violationCount}
          gapCount={gapCount}
          unknownCount={unresolvedCount}
          consumerCount={consumerCount}
          policyCount={policyCount}
          violationRate={violationRate}
          totalQueries={totalQueries}
          systemsMonitored={systemsMonitored}
          topInferredPurposes={topInferredPurposes}
          onUnknownClick={handleReviewUnknown}
        />

        <Divider className="!my-0" />

        {/* Main table */}
        <ViolationsTable
          activeTab={tableTab}
          onInvestigate={setSelectedPolicy}
        />
      </Flex>
    </FixedLayout>
  );
};

export default AccessControlV2Page;
