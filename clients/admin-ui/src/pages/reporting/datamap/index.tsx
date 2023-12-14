import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DatamapReportTable } from "~/features/datamap/reporting/DatamapReportTable";

const DatamapReportingPage = () => (
  <FixedLayout
    title="Datamap Report"
    mainProps={{
      padding: "40px",
      paddingRight: "48px",
    }}
  >
    <DatamapReportTable />
  </FixedLayout>
);

export default DatamapReportingPage;
