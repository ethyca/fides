import { Button, Icons } from "fidesui";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import AssetReportingTable from "~/features/asset-reporting/AssetReportingTable";
import useAssetReportingDownload from "~/features/asset-reporting/hooks/useAssetReportingDownload";
import { useAssetReportingTable } from "~/features/asset-reporting/hooks/useAssetReportingTable";

const AssetReportingPage = () => {
  const { downloadReport, isDownloadingReport } = useAssetReportingDownload();
  const {
    columns,
    searchQuery,
    updateSearch,
    tableProps,
    columnFilters,
  } = useAssetReportingTable({ filters: {} });

  // Build export filters from current table state
  const handleExport = () => {
    downloadReport({
      ...columnFilters,
      search: searchQuery || undefined,
    });
  };

  return (
    <FixedLayout title="Asset reporting">
      <PageHeader
        heading="Asset reporting"
        rightContent={
          <Button
            icon={<Icons.Download />}
            onClick={handleExport}
            loading={isDownloadingReport}
            data-testid="download-asset-report-btn"
          >
            Export CSV
          </Button>
        }
      />
      <AssetReportingTable
        columns={columns}
        searchQuery={searchQuery}
        updateSearch={updateSearch}
        tableProps={tableProps}
      />
    </FixedLayout>
  );
};

export default AssetReportingPage;
