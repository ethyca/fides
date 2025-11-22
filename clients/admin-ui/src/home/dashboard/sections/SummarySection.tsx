import { SimpleGrid } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import * as React from "react";

import { SummaryCard } from "../components/SummaryCard";
import { PrivacyRequestIcon } from "../components/icons/PrivacyRequestIcon";
import { SystemDetectionIcon } from "../components/icons/SystemDetectionIcon";
import { dummyDashboardData } from "../data/dummyData";

/**
 * Summary section component displaying top-level metrics
 * Shows Privacy Requests, System Detection, and Data Classification cards
 */
export const SummarySection = () => {
  const { summary } = dummyDashboardData;

  return (
    <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6}>
      <SummaryCard
        title="Privacy Requests"
        icon={<PrivacyRequestIcon width="26px" height="20px" color={palette.FIDESUI_MINOS} />}
        total={summary.privacyRequests.total}
        totalLabel={summary.privacyRequests.totalLabel}
        breakdown={summary.privacyRequests.breakdown}
        viewAllHref="/privacy-requests"
        leftBorderColor={palette.FIDESUI_SANDSTONE}
      />
      <SummaryCard
        title="System Detection"
        icon={<SystemDetectionIcon width="26px" height="20px" color={palette.FIDESUI_MINOS} />}
        total={summary.systemDetection.total}
        totalLabel={summary.systemDetection.totalLabel}
        breakdown={summary.systemDetection.breakdown}
        viewAllHref="/action-center"
        leftBorderColor={palette.FIDESUI_OLIVE}
      />
      <SummaryCard
        title="Data Classification"
        icon={<SystemDetectionIcon width="26px" height="20px" color={palette.FIDESUI_MINOS} />}
        total={summary.dataClassification.total}
        totalLabel={summary.dataClassification.totalLabel}
        breakdown={summary.dataClassification.breakdown}
        viewAllHref="/action-center"
        leftBorderColor={palette.FIDESUI_TERRACOTTA}
      />
    </SimpleGrid>
  );
};
