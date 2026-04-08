import { Button, Icons } from "fidesui";
import React, { useCallback, useState } from "react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";

import AssetReportingTable from "~/features/asset-reporting/AssetReportingTable";
import useAssetReportingDownload from "~/features/asset-reporting/hooks/useAssetReportingDownload";
import { useAssetReportingTable } from "~/features/asset-reporting/hooks/useAssetReportingTable";
import ErrorPage from "~/features/common/errors/ErrorPage";
import FixedLayout from "~/features/common/FixedLayout";
import { SidePanel } from "~/features/common/SidePanel";
import {
  useDatamapReport,
  DatamapReportProvider,
} from "~/features/datamap/reporting/datamap-report-context";
import DatamapReportSidebarFilters from "~/features/datamap/reporting/DatamapReportSidebarFilters";
import { DatamapReportTable } from "~/features/datamap/reporting/DatamapReportTable";

const VIEWS = {
  DATA_MAP: "data-map",
  ASSET: "asset",
} as const;

const DatamapFilters = () => {
  const { selectedFilters, setSelectedFilters, setSavedCustomReportId } =
    useDatamapReport();

  const activeFilterCount =
    selectedFilters.dataUses.length +
    selectedFilters.dataSubjects.length +
    selectedFilters.dataCategories.length;

  const handleClearAllFilters = useCallback(() => {
    setSavedCustomReportId("");
    setSelectedFilters({
      dataUses: [],
      dataSubjects: [],
      dataCategories: [],
    });
  }, [setSavedCustomReportId, setSelectedFilters]);

  return (
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
  );
};

const ReportsHub = () => {
  const [activeView, setActiveView] = useState<string>(VIEWS.DATA_MAP);
  const [datamapError, setDatamapError] = useState<
    FetchBaseQueryError | SerializedError | null
  >(null);

  const onDatamapError = useCallback(
    (e: FetchBaseQueryError | SerializedError) => {
      setDatamapError(e);
    },
    [],
  );

  // Asset report hooks (always called, but only rendered when active)
  const { downloadReport, isDownloadingReport } = useAssetReportingDownload();
  const { columns, searchQuery, updateSearch, tableProps, columnFilters } =
    useAssetReportingTable({ filters: {} });

  const handleExport = () => {
    downloadReport({ ...columnFilters, search: searchQuery || undefined });
  };

  if (datamapError && activeView === VIEWS.DATA_MAP) {
    return (
      <ErrorPage
        error={datamapError}
        defaultMessage="A problem occurred while fetching the datamap report"
      />
    );
  }

  return (
    <DatamapReportProvider>
      <SidePanel>
        <SidePanel.Identity title="Reports" />
        <SidePanel.Navigation
          items={[
            { key: VIEWS.DATA_MAP, label: "Data Map Report" },
            { key: VIEWS.ASSET, label: "Asset Report" },
          ]}
          activeKey={activeView}
          onSelect={setActiveView}
        />
        {activeView === VIEWS.DATA_MAP && <DatamapFilters />}
        {activeView === VIEWS.ASSET && (
          <>
            <SidePanel.Search
              placeholder="Search assets..."
              onSearch={updateSearch}
              value={searchQuery ?? ""}
              onChange={(e) => updateSearch(e.target.value)}
            />
            <SidePanel.Actions>
              <Button
                icon={<Icons.Download />}
                onClick={handleExport}
                loading={isDownloadingReport}
                data-testid="download-asset-report-btn"
              >
                Export CSV
              </Button>
            </SidePanel.Actions>
          </>
        )}
      </SidePanel>
      <FixedLayout title="Reports">
        {activeView === VIEWS.DATA_MAP && (
          <DatamapReportTable onError={onDatamapError} />
        )}
        {activeView === VIEWS.ASSET && (
          <AssetReportingTable
            columns={columns}
            searchQuery={searchQuery}
            updateSearch={updateSearch}
            tableProps={tableProps}
          />
        )}
      </FixedLayout>
    </DatamapReportProvider>
  );
};

export default ReportsHub;
