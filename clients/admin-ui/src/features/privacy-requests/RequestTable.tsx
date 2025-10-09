import {
  ColumnSort,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  AntButton as Button,
  AntFlex as Flex,
  AntList as List,
  AntPagination as Pagination,
  AntSpin as Spin,
  AntTag as Tag,
  AntText as Text,
  AntTypography as Typography,
  Box,
  BoxProps,
  HStack,
  Icons,
  Portal,
  useDisclosure,
  useToast,
} from "fidesui";
import { useRouter } from "next/router";
import { parseAsString, useQueryState } from "nuqs";
import React, { useCallback, useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";

import { DownloadLightIcon } from "~/features/common/Icon";
import {
  FidesTableV2,
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
import { getRequestTableColumns } from "~/features/privacy-requests/RequestTableColumns";
import { RequestTableFilterModal } from "~/features/privacy-requests/RequestTableFilterModal";
import { PrivacyRequestEntity, Rule } from "~/features/privacy-requests/types";
import { ActionType } from "~/types/api";

import { useAntPagination } from "../common/pagination/useAntPagination";
import RequestStatusBadge from "../common/RequestStatusBadge";
import { SubjectRequestActionTypeMap } from "./constants";
import useDownloadPrivacyRequestReport from "./hooks/useDownloadPrivacyRequestReport";

const Label = ({ children }: React.PropsWithChildren) => {
  return <Text type="secondary">{children}</Text>;
};

const getActionTypesFromRules = (rules: Rule[]): ActionType[] =>
  Array.from(
    new Set(
      rules
        .filter((rule) => Object.values(ActionType).includes(rule.action_type))
        .map((rule) => rule.action_type),
    ),
  );

type LabeledProps = React.PropsWithChildren<{ label: React.ReactNode }>;

const LabeledTag = ({ label, children }: LabeledProps) => {
  return (
    <Flex gap={8}>
      <Label>{label}:</Label>
      <Tag>{children}</Tag>
    </Flex>
  );
};

const LabeledText = ({ label, children }: LabeledProps) => {
  return (
    <Flex gap={4}>
      <Label>{label}:</Label>
      <Text>{children}</Text>
    </Flex>
  );
};

export const RequestTable = ({ ...props }: BoxProps): JSX.Element => {
  const [fuzzySearchTerm, setFuzzySearchTerm] = useQueryState(
    "search",
    parseAsString.withDefault("").withOptions({ throttleMs: 100 }),
  );
  const filters = useSelector(selectPrivacyRequestFilters);
  const toast = useToast();
  const router = useRouter();
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

  const handleViewDetails = (id: string) => {
    const url = `/privacy-requests/${id}`;
    router.push(url);
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

  const tableInstance = useReactTable<PrivacyRequestEntity>({
    getCoreRowModel: getCoreRowModel(),
    data: requests,
    columns: useMemo(() => getRequestTableColumns(), []),
    getRowId: (row) => `${row.status}-${row.id}`,
    manualPagination: true,
    columnResizeMode: "onChange",
  });

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
          <TableSkeletonLoader rowHeight={26} numRows={10} />
        </Box>
      ) : (
        <Flex vertical gap="middle">
          {/* <FidesTableV2<PrivacyRequestEntity>
            tableInstance={tableInstance}
            onRowClick={(row) => handleViewDetails(row.id)}
            onSort={handleSort}
            loading={isFetching}
          /> */}
          <Spin spinning={isLoading || isFetching}>
            <List<PrivacyRequestEntity>
              bordered
              dataSource={requests}
              renderItem={(item) => {
                return (
                  <List.Item actions={[<Button key="test">test</Button>]}>
                    <List.Item.Meta
                      title={
                        <div
                          style={{
                            display: "flex",
                            gap: "16px",
                          }}
                        >
                          <Text
                            copyable={{
                              text: item.id,
                              icon: <Icons.Copy style={{ marginTop: "4px" }} />,
                            }}
                            style={{ display: "flex", gap: "8px" }}
                          >
                            {item.policy.name}
                          </Text>
                          <div>
                            <RequestStatusBadge
                              status={item.status}
                              style={{ fontWeight: "normal" }}
                            />
                          </div>
                        </div>
                      }
                      description={
                        <Flex vertical gap={8} style={{ paddingTop: 4 }}>
                          <Flex gap={8}>
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
