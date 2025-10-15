import {
  AntButton as Button,
  AntFlex as Flex,
  AntList as List,
  AntMessage as message,
  AntPagination as Pagination,
  AntSkeleton as Skeleton,
  AntSpin as Spin,
  Portal,
  useDisclosure,
} from "fidesui";
import { parseAsString, useQueryState } from "nuqs";
import React, { useCallback, useMemo, useState } from "react";
import { useSelector } from "react-redux";

import { BulkActionsDropdown } from "~/features/common/BulkActionsDropdown";
import { DownloadLightIcon } from "~/features/common/Icon";
import { GlobalFilterV2, TableActionBar } from "~/features/common/table/v2";
import {
  selectPrivacyRequestFilters,
  useGetAllPrivacyRequestsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";
import { RequestTableFilterModal } from "~/features/privacy-requests/RequestTableFilterModal";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

import { useAntPagination } from "../../common/pagination/useAntPagination";
import useDownloadPrivacyRequestReport from "../hooks/useDownloadPrivacyRequestReport";
import { usePrivacyRequestBulkActions } from "../hooks/usePrivacyRequestBulkActions";
import { ListItem } from "./list-item/ListItem";

export const PrivacyRequestsDashboard = () => {
  const [fuzzySearchTerm, setFuzzySearchTerm] = useQueryState(
    "search",
    parseAsString.withDefault("").withOptions({ throttleMs: 100 }),
  );
  const filters = useSelector(selectPrivacyRequestFilters);
  const [messageApi, messageContext] = message.useMessage();
  const [selectedRequestKeys, setSelectedRequestKeys] = useState<React.Key[]>(
    [],
  );

  const pagination = useAntPagination();
  const { pageIndex, pageSize, resetPagination } = pagination;

  const { isOpen, onOpen, onClose } = useDisclosure();

  const { data, isLoading, isFetching } = useGetAllPrivacyRequestsQuery({
    ...filters,
    page: pageIndex,
    size: pageSize,
    fuzzy_search_str: fuzzySearchTerm,
  });
  const { items: requests, total: totalRows } = useMemo(() => {
    const results = data || { items: [], total: 0, pages: 0 };
    // Add explicit key property for Ant Design List selection
    const itemsWithKeys = results.items.map((item) => ({
      ...item,
      key: item.id,
    }));

    return { ...results, items: itemsWithKeys };
  }, [data]);

  const { downloadReport } = useDownloadPrivacyRequestReport();

  const handleSearch = useCallback(
    (searchTerm: string) => {
      setFuzzySearchTerm(searchTerm ?? "");
      resetPagination();
    },
    [resetPagination, setFuzzySearchTerm],
  );

  const handleExport = async () => {
    let messageStr;
    try {
      await downloadReport(filters);
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

  // Get selected requests from the list
  const selectedRequests = useMemo(
    () =>
      requests.filter((request) => selectedRequestKeys.includes(request.id)),
    [requests, selectedRequestKeys],
  );

  const { bulkActionMenuItems } = usePrivacyRequestBulkActions({
    selectedRequests,
    onApprove: () => {
      // TODO: Implement approve functionality
      // eslint-disable-next-line no-console
      console.log("Approve clicked for:", selectedRequestKeys);
    },
    onDeny: () => {
      // TODO: Implement deny functionality
      // eslint-disable-next-line no-console
      console.log("Deny clicked for:", selectedRequestKeys);
    },
    onFinalize: () => {
      // TODO: Implement finalize functionality
      // eslint-disable-next-line no-console
      console.log("Finalize clicked for:", selectedRequestKeys);
    },
    onDelete: () => {
      // TODO: Implement delete functionality
      // eslint-disable-next-line no-console
      console.log("Delete clicked for:", selectedRequestKeys);
    },
  });

  return (
    <div>
      <TableActionBar>
        <GlobalFilterV2
          globalFilter={fuzzySearchTerm}
          setGlobalFilter={handleSearch}
          placeholder="Search by request ID or identity value"
        />
        <div className="flex items-center gap-2">
          <BulkActionsDropdown
            selectedIds={selectedRequestKeys}
            menuItems={bulkActionMenuItems}
          />
          <Button data-testid="filter-btn" onClick={onOpen}>
            Filter
          </Button>
          <Button
            aria-label="Export report"
            data-testid="export-btn"
            icon={<DownloadLightIcon ml="1.5px" />}
            onClick={handleExport}
          />
        </div>
        <Portal>
          <RequestTableFilterModal
            isOpen={isOpen}
            onClose={onClose}
            onFilterChange={resetPagination}
          />
        </Portal>
      </TableActionBar>
      {isLoading ? (
        <div className="border p-2">
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
            <List<PrivacyRequestEntity>
              bordered
              dataSource={requests}
              rowSelection={{
                selectedRowKeys: selectedRequestKeys,
                onChange: (keys) => {
                  setSelectedRequestKeys(keys);
                },
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
            align="end"
          />
        </Flex>
      )}
      {messageContext}
    </div>
  );
};
