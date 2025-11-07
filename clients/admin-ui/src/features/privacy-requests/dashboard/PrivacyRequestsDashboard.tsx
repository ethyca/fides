import {
  AntButton as Button,
  AntCheckbox as Checkbox,
  AntFlex as Flex,
  AntList as List,
  AntMessage as message,
  AntModal as modal,
  AntPagination as Pagination,
  AntSkeleton as Skeleton,
  AntSpin as Spin,
  AntTypography as Typography,
  Icons,
  Portal,
  useDisclosure,
} from "fidesui";
import React, { useMemo } from "react";

import { BulkActionsDropdown } from "~/features/common/BulkActionsDropdown";
import { useSelection } from "~/features/common/hooks/useSelection";
import {
  useLazyDownloadPrivacyRequestCsvV2Query,
  useSearchPrivacyRequestsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";
import { PrivacyRequestResponse } from "~/types/api";

import { useAntPagination } from "../../common/pagination/useAntPagination";
import { AdvancedSearchModal } from "./AdvancedSearchModal";
import { usePrivacyRequestBulkActions } from "./hooks/usePrivacyRequestBulkActions";
import usePrivacyRequestsFilters from "./hooks/usePrivacyRequestsFilters";
import { ListItem } from "./list-item/ListItem";
import { PrivacyRequestFiltersBar } from "./PrivacyRequestFiltersBar";

export const PrivacyRequestsDashboard = () => {
  const pagination = useAntPagination();
  const {
    filterQueryParams,
    fuzzySearchTerm,
    setFuzzySearchTerm,
    modalFilters,
    setModalFilters,
  } = usePrivacyRequestsFilters({
    pagination,
  });

  const [messageApi, messageContext] = message.useMessage();
  const [modalApi, modalContext] = modal.useModal();

  const { selectedIds, setSelectedIds, clearSelectedIds } = useSelection();

  const {
    isOpen: isAdvancedSearchOpen,
    onOpen: onOpenAdvancedSearch,
    onClose: onCloseAdvancedSearch,
  } = useDisclosure();

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

  const [downloadReport] = useLazyDownloadPrivacyRequestCsvV2Query();

  const handleExport = async () => {
    let messageStr;
    try {
      await downloadReport(filterQueryParams);
    } catch (error) {
      if (error instanceof Error) {
        messageStr = error.message;
      } else {
        messageStr = "Unknown error occurred";
      }
    }
    if (messageStr) {
      messageApi.error(messageStr, 5000);
    }
  };

  const { bulkActionMenuItems } = usePrivacyRequestBulkActions({
    requests,
    selectedIds,
    clearSelectedIds,
    messageApi,
    modalApi,
  });

  // Select all logic
  const currentPageIds = useMemo(
    () => requests.map((item) => item.id),
    [requests],
  );

  const allCurrentPageSelected = useMemo(
    () =>
      currentPageIds.length > 0 &&
      currentPageIds.every((id) => selectedIds.includes(id)),
    [currentPageIds, selectedIds],
  );

  const someCurrentPageSelected = useMemo(
    () =>
      currentPageIds.some((id) => selectedIds.includes(id)) &&
      !allCurrentPageSelected,
    [currentPageIds, selectedIds, allCurrentPageSelected],
  );

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      // Select all items on current page
      const newSelected = Array.from(
        new Set([...selectedIds, ...currentPageIds]),
      );
      setSelectedIds(newSelected);
    } else {
      // Deselect all items
      setSelectedIds([]);
    }
  };

  return (
    <div>
      {/* First row: Search and Filters */}
      <Flex gap="small" align="center" className="mb-2">
        <PrivacyRequestFiltersBar
          modalFilters={modalFilters}
          setModalFilters={setModalFilters}
          onOpenAdvancedSearch={onOpenAdvancedSearch}
          fuzzySearchTerm={fuzzySearchTerm}
          setFuzzySearchTerm={setFuzzySearchTerm}
        />
      </Flex>

      {/* Second row: Select all and actions */}
      <Flex gap="small" align="center" justify="space-between" className="mb-4">
        <Flex gap="small" align="center">
          <Checkbox
            id="select-all-privacy-requests"
            checked={allCurrentPageSelected}
            indeterminate={someCurrentPageSelected}
            onChange={(e) => handleSelectAll(e.target.checked)}
            data-testid="select-all-checkbox"
          />
          <label htmlFor="select-all-privacy-requests">Select all</label>
        </Flex>

        <Flex gap="small" align="center">
          {selectedIds.length > 0 && (
            <>
              <Typography.Text strong>
                {selectedIds.length} selected
              </Typography.Text>
              <Typography.Text> / </Typography.Text>
            </>
          )}
          <Typography.Text>{totalRows ?? 0} results</Typography.Text>
          <BulkActionsDropdown
            selectedIds={selectedIds}
            menuItems={bulkActionMenuItems}
            showSelectedCount={false}
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
            onClick={handleExport}
          />
        </Flex>
      </Flex>

      <Portal>
        <AdvancedSearchModal
          open={isAdvancedSearchOpen}
          onClose={onCloseAdvancedSearch}
        />
      </Portal>
      {isLoading ? (
        <div className=" p-2">
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
      {messageContext}
      {modalContext}
    </div>
  );
};
