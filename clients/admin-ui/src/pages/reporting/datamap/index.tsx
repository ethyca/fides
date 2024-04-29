import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DatamapReportTable } from "~/features/datamap/reporting/DatamapReportTable";

const DatamapReportingPage = () => (
  <FixedLayout
    title="Datamap Report"
    mainProps={{
      padding: "24px 40px",
    }}
  >
    <DatamapReportTable />
  </FixedLayout>
);

export default DatamapReportingPage;
