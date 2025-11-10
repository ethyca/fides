import {
  AntButton as Button,
  AntFlex as Flex,
  AntList as List,
  AntMessage as message,
  AntModal as modal,
  AntPagination as Pagination,
  AntSkeleton as Skeleton,
  AntSpin as Spin,
  Icons,
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

  return (
    <div>
      {/* First row: Search and Filters */}
      <Flex gap="small" align="center" className="mb-4">
        <PrivacyRequestFiltersBar
          modalFilters={modalFilters}
          setModalFilters={setModalFilters}
          fuzzySearchTerm={fuzzySearchTerm}
          setFuzzySearchTerm={setFuzzySearchTerm}
        />
      </Flex>

      {/* Second row: Actions */}
      <Flex gap="small" align="center" justify="flex-end" className="mb-2">
        <BulkActionsDropdown
          selectedIds={selectedIds}
          menuItems={bulkActionMenuItems}
          totalResults={totalRows ?? 0}
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
