import {
  ColumnSort,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { formatDistance } from "date-fns";
import dayjs from "dayjs";
import {
  AntButton as Button,
  AntCol as Col,
  AntFlex as Flex,
  AntList as List,
  AntPagination as Pagination,
  AntRow as Row,
  AntSkeleton as Skeleton,
  AntSpin as Spin,
  AntTag as Tag,
  AntText as Text,
  AntTooltip as Tooltip,
  Box,
  BoxProps,
  HStack,
  Icons,
  Portal,
  useDisclosure,
  useToast,
} from "fidesui";
import Link from "next/link";
import { useRouter } from "next/router";
import { parseAsString, useQueryState } from "nuqs";
import React, { useCallback, useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";

import { DownloadLightIcon } from "~/features/common/Icon";
import {
  GlobalFilterV2,
  TableActionBar,
  TableSkeletonLoader,
} from "~/features/common/table/v2";
import {
  clearSortKeys,
  selectPrivacyRequestFilters,
  setSortDirection,
  setSortKey,
  useGetAllPrivacyRequestsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";
import { RequestTableFilterModal } from "~/features/privacy-requests/RequestTableFilterModal";
import { PrivacyRequestEntity, Rule } from "~/features/privacy-requests/types";
import { ActionType, PrivacyRequestStatus } from "~/types/api";

import { useAntPagination } from "../common/pagination/useAntPagination";
import RequestStatusBadge from "../common/RequestStatusBadge";
import { formatDate, sentenceCase } from "../common/utils";
import { SubjectRequestActionTypeMap } from "./constants";
import useDownloadPrivacyRequestReport from "./hooks/useDownloadPrivacyRequestReport";
import { RequestTableActions } from "./RequestTableActions";
import { LabeledTag, LabeledText } from "./dashboard/labels";
import { DaysLeft } from "./dashboard/daysLeft";

const getActionTypesFromRules = (rules: Rule[]): ActionType[] =>
  Array.from(
    new Set(
      rules
        .filter((rule) => Object.values(ActionType).includes(rule.action_type))
        .map((rule) => rule.action_type),
    ),
  );

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
                      <Link
                        key="view"
                        legacyBehavior
                        href={`/privacy-requests/${encodeURIComponent(item.id)}`}
                      >
                        <Tooltip title="View privacy request">
                          <Button
                            key="test"
                            icon={<Icons.View />}
                            aria-label="View Request"
                            size="small"
                            href={`/privacy-requests/${encodeURIComponent(item.id)}`}
                          />
                        </Tooltip>
                      </Link>,
                      <RequestTableActions subjectRequest={item} />,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Flex gap={16} wrap>
                          <Text
                            copyable={{
                              text: item.id,
                              icon: (
                                <Tooltip title="Copy request ID">
                                  <Icons.Copy style={{ marginTop: "4px" }} />
                                </Tooltip>
                              ),
                              tooltips: null,
                            }}
                            style={{
                              display: "flex",
                              gap: "8px",
                              minWidth: "100px",
                            }}
                          >
                            {item.policy.name}
                          </Text>
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
                            {(item.identity.email?.value ?? "").length > 0 ? (
                              <LabeledText label="Email">
                                {item.identity.email.value}
                              </LabeledText>
                            ) : null}

                            {getActionTypesFromRules(item.policy.rules)
                              .map((actionType) =>
                                SubjectRequestActionTypeMap.get(actionType),
                              )
                              .map((actionType) => (
                                <Tag key={actionType}>{actionType}</Tag>
                              ))}
                          </Flex>

                          <Flex wrap gap={16}>
                            {Object.entries(item.identity)
                              .filter(
                                ([key, identity]) =>
                                  identity.value && key !== "email",
                              )
                              .map(([key, identity]) => (
                                <LabeledTag key={key} label={identity.label}>
                                  {identity.value}
                                </LabeledTag>
                              ))}
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
                      <LabeledText label="Received">
                        <Text type="secondary">
                          {sentenceCase(
                            formatDistance(
                              new Date(item.created_at),
                              new Date(),
                              {
                                addSuffix: true,
                              },
                            ),
                          )}
                        </Text>
                      </LabeledText>
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
