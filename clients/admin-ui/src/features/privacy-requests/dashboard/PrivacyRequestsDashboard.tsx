import {
  Button,
  Checkbox,
  Flex,
  Icons,
  List,
  Pagination,
  Skeleton,
  Spin,
} from "fidesui";
import React, { useEffect, useMemo } from "react";

import { BulkActionsDropdown } from "~/features/common/BulkActionsDropdown";
import { useSelection } from "~/features/common/hooks/useSelection";
import { ResultsSelectedCount } from "~/features/common/ResultsSelectedCount";
import { useSearchPrivacyRequestsQuery } from "~/features/privacy-requests/privacy-requests.slice";
import { PrivacyRequestResponse } from "~/types/api";

import { useAntPagination } from "../../common/pagination/useAntPagination";
import { DuplicateRequestsButton } from "./DuplicateRequestsButton";
import useDownloadPrivacyRequestReport from "./hooks/useDownloadPrivacyRequestReport";
import { usePrivacyRequestBulkActions } from "./hooks/usePrivacyRequestBulkActions";
import usePrivacyRequestsFilters from "./hooks/usePrivacyRequestsFilters";
import { ListItem } from "./list-item/ListItem";
import { PrivacyRequestFiltersBar } from "./PrivacyRequestFiltersBar";

export const PrivacyRequestsDashboard = () => {
  const pagination = useAntPagination();
  const { filterQueryParams, filters, setFilters, sortState, setSortState } =
    usePrivacyRequestsFilters({
      pagination,
    });

  const { data, isLoading, isFetching, refetch } =
    useSearchPrivacyRequestsQuery({
      ...filterQueryParams,
      page: pagination.pageIndex,
      size: pagination.pageSize,
    });

  const { items: requests, total: totalRows } = useMemo(() => {
    const results = data || { items: [], total: 0, pages: 0 };
    const itemsWithKeys = results.items.map((item) => ({
      ...item,
      key: item.id,
    }));

    return { ...results, items: itemsWithKeys };
  }, [data]);

  const {
    selectedIds,
    setSelectedIds,
    clearSelectedIds,
    checkboxSelectState,
    handleSelectAll,
  } = useSelection({
    currentPageKeys: requests.map((request) => request.id),
  });

  // Clear selections when requests change
  // Once we have full support for select all, we can reset this only on filter changes and add a
  // manual clear selection after a bulk action is performed
  useEffect(() => {
    clearSelectedIds();
  }, [requests, clearSelectedIds]);

  const { downloadReport, isDownloadingReport } =
    useDownloadPrivacyRequestReport();

  const { bulkActionMenuItems } = usePrivacyRequestBulkActions({
    requests,
    selectedIds,
  });

  return (
    <div>
      {/* First row: Search and Filters */}
      <Flex gap="small" align="center" className="mb-4">
        <PrivacyRequestFiltersBar
          filters={filters}
          setFilters={setFilters}
          sortState={sortState}
          setSortState={setSortState}
        />
      </Flex>

      {/* Second row: Actions */}
      <Flex gap="small" align="center" justify="space-between" className="mb-2">
        <Flex align="center" gap="small">
          <Checkbox
            id="select-all"
            checked={checkboxSelectState === "checked"}
            indeterminate={checkboxSelectState === "indeterminate"}
            onChange={(e) => handleSelectAll(e.target.checked)}
          />
          <label htmlFor="select-all" className="cursor-pointer">
            Select all
          </label>
          <div className="ml-3">
            <ResultsSelectedCount
              selectedIds={selectedIds}
              totalResults={totalRows ?? 0}
            />
          </div>
        </Flex>
        <Flex align="center" gap="small">
          <DuplicateRequestsButton
            className="ml-3"
            currentStatusFilter={filters.status}
          />
          <BulkActionsDropdown
            selectedIds={selectedIds}
            menuItems={bulkActionMenuItems}
          />
          <Button
            aria-label="Reload"
            data-testid="reload-btn"
            icon={<Icons.Renew />}
            onClick={() => refetch()}
          />
          <Button
            aria-label="Export report"
            data-testid="export-btn"
            icon={<Icons.Download />}
            onClick={() => downloadReport(filterQueryParams)}
            loading={isDownloadingReport}
          />
        </Flex>
      </Flex>

      {isLoading ? (
        <div className="p-2">
          <List
            dataSource={Array(25).fill({})} // Is there a better way to do this?
            renderItem={() => (
              <List.Item>
                <Skeleton />
              </List.Item>
            )}
          />
        </div>
      ) : (
        <Flex vertical gap="middle">
          <Spin spinning={isFetching}>
            <List<PrivacyRequestResponse>
              dataSource={requests}
              rowSelection={{
                selectedRowKeys: selectedIds,
                onChange: setSelectedIds,
              }}
              renderItem={(item, index, checkbox) => (
                <ListItem item={item} checkbox={checkbox} />
              )}
            />
          </Spin>
          <Pagination
            {...pagination.paginationProps}
            showTotal={(total, range) =>
              `${range[0]}-${range[1]} of ${total} items`
            }
            total={totalRows ?? 0}
            align="start"
          />
        </Flex>
      )}
    </div>
  );
};
