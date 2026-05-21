/**
 * Standalone mockup page — visit /consent/reporting/analytics-mockup
 * to preview the Consent Analytics Widget in isolation.
 *
 * Delete this file before merging to main.
 */

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import ConsentAnalyticsWidgetMockup from "~/features/consent-reporting/ConsentAnalyticsWidgetMockup";

const AnalyticsMockupPage = () => {
  return (
    <FixedLayout title="Consent Analytics — Design Mockup">
      <PageHeader
        heading="Consent Analytics"
        breadcrumbItems={[
          { title: "Consent" },
          { title: "Reporting" },
          { title: "Analytics (Mockup)" },
        ]}
      />
      <ConsentAnalyticsWidgetMockup />
    </FixedLayout>
  );
};

export default AnalyticsMockupPage;
