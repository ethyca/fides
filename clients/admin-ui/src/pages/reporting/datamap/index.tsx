import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import React, { useCallback, useState } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import { DatamapReportProvider } from "~/features/datamap/reporting/datamap-report-context";
import { DatamapReportTable } from "~/features/datamap/reporting/DatamapReportTable";

const DatamapReportingPage = () => {
  const [error, setError] = useState<
    FetchBaseQueryError | SerializedError | null
  >(null);

  const onError = useCallback((e: FetchBaseQueryError | SerializedError) => {
    setError(e);
  }, []);

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching the datamap report"
      />
    );
  }
  return (
    <FixedLayout title="Datamap Report">
      <PageHeader
        data-testid="datamap-report-heading"
        heading="Data map report"
      />
      <DatamapReportProvider>
        <DatamapReportTable onError={onError} />
      </DatamapReportProvider>
    </FixedLayout>
  );
};

export default DatamapReportingPage;
