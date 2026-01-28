import { ColumnsType, Flex, Table, TableProps } from "fidesui";
import React from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { Asset } from "~/types/api";

interface AssetReportingTableProps {
  columns: ColumnsType<Asset>;
  searchQuery?: string;
  updateSearch: (searchQuery: string) => void;
  tableProps: Partial<TableProps<Asset>>;
}

const AssetReportingTable = ({
  columns,
  searchQuery,
  updateSearch,
  tableProps,
}: AssetReportingTableProps) => {
  return (
    <>
      <Flex
        justify="space-between"
        align="center"
        className="sticky -top-6 z-10 mb-4 bg-white py-4"
      >
        <DebouncedSearchInput
          value={searchQuery ?? ""}
          onChange={updateSearch}
          placeholder="Search by asset name or domain..."
          data-testid="asset-search-input"
        />
      </Flex>
      <Table
        {...tableProps}
        columns={columns}
        data-testid="asset-reporting-table"
      />
    </>
  );
};

export default AssetReportingTable;
