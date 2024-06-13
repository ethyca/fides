import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import DetectionResultTable from "~/features/data-discovery-and-detection/tables/DetectionResultTable";

const DataDetectionActivityPage = () => (
  <FixedLayout
    title="Data detection"
    mainProps={{
      padding: "0 40px 48px",
    }}
  >
    <PageHeader
      breadcrumbs={[
        { title: "Data detection", isOpaque: true },
        { title: "All activity" },
      ]}
    />
    <DetectionResultTable />
  </FixedLayout>
);

export default DataDetectionActivityPage;
