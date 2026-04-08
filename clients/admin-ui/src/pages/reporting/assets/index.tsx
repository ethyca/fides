import { Button, Icons } from "fidesui";
import React from "react";

import AssetReportingTable from "~/features/asset-reporting/AssetReportingTable";
import useAssetReportingDownload from "~/features/asset-reporting/hooks/useAssetReportingDownload";
import { useAssetReportingTable } from "~/features/asset-reporting/hooks/useAssetReportingTable";
import FixedLayout from "~/features/common/FixedLayout";
import { SidePanel } from "~/features/common/SidePanel";

const AssetReportingPage = () => {
  const { downloadReport, isDownloadingReport } = useAssetReportingDownload();
  const { columns, searchQuery, updateSearch, tableProps, columnFilters } =
    useAssetReportingTable({ filters: {} });

  // Build export filters from current table state
  const handleExport = () => {
    downloadReport({
      ...columnFilters,
      search: searchQuery || undefined,
    });
  };

  return (
    <>
      <SidePanel>
        <SidePanel.Identity title="Asset report" />
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
      </SidePanel>
      <FixedLayout title="Asset report">
        <AssetReportingTable
          columns={columns}
          searchQuery={searchQuery}
          updateSearch={updateSearch}
          tableProps={tableProps}
        />
      </FixedLayout>
    </>
  );
};

export default AssetReportingPage;
