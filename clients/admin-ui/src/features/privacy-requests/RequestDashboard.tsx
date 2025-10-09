import { ColumnSort } from "@tanstack/react-table";
import {
  AntButton as Button,
  AntFlex as Flex,
  AntList as List,
  AntPagination as Pagination,
  AntSkeleton as Skeleton,
  AntSpin as Spin,
  Box,
  BoxProps,
  HStack,
  Portal,
  useDisclosure,
  useToast,
} from "fidesui";
import { parseAsString, useQueryState } from "nuqs";
import React, { useCallback, useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";

import { DownloadLightIcon } from "~/features/common/Icon";
import { GlobalFilterV2, TableActionBar } from "~/features/common/table/v2";
import {
  clearSortKeys,
  selectPrivacyRequestFilters,
  setSortDirection,
  setSortKey,
  useGetAllPrivacyRequestsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";
import { RequestTableFilterModal } from "~/features/privacy-requests/RequestTableFilterModal";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

import { useAntPagination } from "../common/pagination/useAntPagination";
import RequestStatusBadge from "../common/RequestStatusBadge";

import useDownloadPrivacyRequestReport from "./hooks/useDownloadPrivacyRequestReport";
import { RequestTableActions } from "./RequestTableActions";
import { DaysLeft } from "./dashboard/DaysLeft";
import { ReceivedOn } from "./dashboard/RevievedOn";
import { EmailIdentity, NonEmailIdentities } from "./dashboard/identities";
import { PolicyActionTypes } from "./dashboard/PolicyActionTypes";
import { RequestTitle } from "./dashboard/RequestTitle";
import { ViewButton } from "./dashboard/listButtons";

export const RequestDashboard = ({ ...props }: BoxProps): JSX.Element => {
  const [fuzzySearchTerm, setFuzzySearchTerm] = useQueryState(
    "search",
    parseAsString.withDefault("").withOptions({ throttleMs: 100 }),
  );
  const filters = useSelector(selectPrivacyRequestFilters);
  const toast = useToast();
  const dispatch = useDispatch();

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

    return results;
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
    let message;
    try {
      await downloadReport(filters);
    } catch (error) {
      if (error instanceof Error) {
        message = error.message;
      } else {
        message = "Unknown error occurred";
      }
    }
    if (message) {
      toast({
        description: `${message}`,
        duration: 5000,
        status: "error",
      });
    }
  };

  const handleSort = (columnSort: ColumnSort) => {
    if (!columnSort) {
      dispatch(clearSortKeys());
      return;
    }
    const { id, desc } = columnSort;
    dispatch(setSortKey(id));
    dispatch(setSortDirection(desc ? "desc" : "asc"));
    resetPagination();
  };

  return (
    <Box {...props}>
      <TableActionBar>
        <GlobalFilterV2
          globalFilter={fuzzySearchTerm}
          setGlobalFilter={handleSearch}
          placeholder="Search by request ID or identity value"
        />
        <HStack alignItems="center" spacing={2}>
          <Button data-testid="filter-btn" onClick={onOpen}>
            Filter
          </Button>
          <Button
            aria-label="Export report"
            data-testid="export-btn"
            icon={<DownloadLightIcon ml="1.5px" />}
            onClick={handleExport}
          />
        </HStack>
        <Portal>
          <RequestTableFilterModal
            isOpen={isOpen}
            onClose={onClose}
            onFilterChange={resetPagination}
          />
        </Portal>
      </TableActionBar>
      {isLoading ? (
        <Box p={2} borderWidth={1}>
          <List
            dataSource={Array(25).fill({})} // Is there a better way to do this?
            renderItem={() => (
              <List.Item>
                <Skeleton></Skeleton>
              </List.Item>
            )}
          ></List>
        </Box>
      ) : (
        <Flex vertical gap="middle">
          <Spin spinning={isFetching}>
            <List<PrivacyRequestEntity>
              style={{ borderTopRightRadius: 0, borderTopLeftRadius: 0 }}
              bordered
              dataSource={requests}
              renderItem={(item) => {
                return (
                  <List.Item
                    styles={{
                      actions: {
                        minWidth: "150px",
                        display: "flex",
                        justifyContent: "right",
                      },
                    }}
                    actions={[
                      <ViewButton key="view" id={item.id} />,
                      <RequestTableActions subjectRequest={item} />,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Flex gap={16} wrap>
                          <RequestTitle
                            id={item.id}
                            policyName={item.policy.name}
                          />
                          {/* why does this div give better alignment */}
                          <div>
                            <RequestStatusBadge
                              status={item.status}
                              style={{ fontWeight: "normal" }}
                            />
                          </div>
                        </Flex>
                      }
                      description={
                        <Flex vertical gap={16} style={{ paddingTop: 4 }} wrap>
                          <Flex gap={8} wrap>
                            <EmailIdentity value={item.identity.email?.value} />
                            <PolicyActionTypes rules={item.policy.rules} />
                          </Flex>

                          <Flex wrap gap={16}>
                            <NonEmailIdentities identities={item.identity} />
                          </Flex>
                        </Flex>
                      }
                    />
                    <Flex gap={16} wrap>
                      <DaysLeft
                        daysLeft={item.days_left}
                        status={item.status}
                        timeframe={item.policy.execution_timeframe}
                      />
                      <ReceivedOn createdAt={item.created_at} />
                    </Flex>
                  </List.Item>
                );
              }}
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
    </Box>
  );
};
