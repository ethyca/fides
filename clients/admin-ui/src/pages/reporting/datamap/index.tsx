import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import React, { useCallback, useState } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import {
  useDatamapReport,
  DatamapReportProvider,
} from "~/features/datamap/reporting/datamap-report-context";
import DatamapReportSidebarFilters from "~/features/datamap/reporting/DatamapReportSidebarFilters";
import { DatamapReportTable } from "~/features/datamap/reporting/DatamapReportTable";

const DatamapReportingPageContent = () => {
  const [error, setError] = useState<
    FetchBaseQueryError | SerializedError | null
  >(null);

  const { selectedFilters, setSelectedFilters, setSavedCustomReportId } =
    useDatamapReport();

  const activeFilterCount =
    selectedFilters.dataUses.length +
    selectedFilters.dataSubjects.length +
    selectedFilters.dataCategories.length;

  const onError = useCallback((e: FetchBaseQueryError | SerializedError) => {
    setError(e);
  }, []);

  const handleClearAllFilters = useCallback(() => {
    setSavedCustomReportId("");
    setSelectedFilters({
      dataUses: [],
      dataSubjects: [],
      dataCategories: [],
    });
  }, [setSavedCustomReportId, setSelectedFilters]);

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching the datamap report"
      />
    );
  }

  return (
    <>
      <SidePanel>
        <SidePanel.Identity title="Data map report" />
        <SidePanel.Filters
          activeCount={activeFilterCount}
          onClearAll={handleClearAllFilters}
        >
          <DatamapReportSidebarFilters
            selectedFilters={selectedFilters}
            onFilterChange={(newFilters) => {
              setSavedCustomReportId("");
              setSelectedFilters(newFilters);
            }}
          />
        </SidePanel.Filters>
      </SidePanel>
      <Layout title="Datamap Report">
        <DatamapReportTable onError={onError} />
      </Layout>
    </>
  );
};

const DatamapReportingPage = () => (
  <DatamapReportProvider>
    <DatamapReportingPageContent />
  </DatamapReportProvider>
);

export default DatamapReportingPage;
