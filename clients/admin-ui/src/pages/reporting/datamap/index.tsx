import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import { DatamapReportProvider } from "~/features/datamap/reporting/datamap-report-context";
import { DatamapReportTable } from "~/features/datamap/reporting/DatamapReportTable";

const DatamapReportingPage = () => (
  <FixedLayout title="Datamap Report">
    <PageHeader
      data-testid="datamap-report-heading"
      heading="Data map report"
    />
    <DatamapReportProvider>
      <DatamapReportTable />
    </DatamapReportProvider>
  </FixedLayout>
);

export default DatamapReportingPage;
