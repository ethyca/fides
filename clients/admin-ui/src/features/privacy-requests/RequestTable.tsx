import {
  ColumnSort,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  AntButton as Button,
  AntFlex as Flex,
  Box,
  BoxProps,
  HStack,
  Portal,
  useDisclosure,
  useToast,
  AntList as List,
  AntTypography as Typography,
  AntCard as Card,
  AntTag as Tag,
  AntSpin as Spin,
  AntTooltip as Tooltip,
  AntRow as Row,
  AntCol as Col,
  Icons,
  AntDivider as Divider,
} from "fidesui";
import { formatDate, sentenceCase } from "~/features/common/utils";
import { useRouter } from "next/router";
import { parseAsString, useQueryState } from "nuqs";
import { useCallback, useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";
import { SubjectRequestActionTypeMap } from "~/features/privacy-requests/constants";
import { Badge } from "antd";

import { selectToken } from "~/features/auth";
import { useFeatures } from "~/features/common/features";
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

import AntPaginator from "../common/pagination/AntPaginator";
import { useAntPaginationContext } from "../common/pagination/PaginationProvider";
import useDownloadPrivacyRequestReport from "./hooks/useDownloadPrivacyRequestReport";
import RequestStatusBadge, {
  statusPropMap,
} from "../common/RequestStatusBadge";
import { Descriptions, Space } from "antd";
import { ActionType, PrivacyRequestStatus } from "~/types/api";
import { formatDistance } from "date-fns";
import Link from "next/link";
import dayjs from "dayjs";

const getActionTypesFromRules = (rules: Rule[]): ActionType[] =>
  Array.from(
    new Set(
      rules
        .filter((rule) => Object.values(ActionType).includes(rule.action_type))
        .map((rule) => rule.action_type),
    ),
  );

const DAY_IRRELEVANT_STATUSES = [
  PrivacyRequestStatus.COMPLETE,
  PrivacyRequestStatus.CANCELED,
  PrivacyRequestStatus.DENIED,
  PrivacyRequestStatus.IDENTITY_UNVERIFIED,
];

const DaysLeft = ({
  status,
  daysLeft,
  timeframe = 45,
}: {
  status: PrivacyRequestStatus;
  daysLeft: number | undefined;
  timeframe: number | undefined;
}) => {
  const showBadge =
    !DAY_IRRELEVANT_STATUSES.includes(status) && daysLeft !== undefined;

  if (showBadge) {
    const percentage = (100 * daysLeft) / timeframe;
    let color = "error";
    if (percentage < 25) {
      color = "error";
    } else if (percentage >= 75) {
      color = "success";
    } else {
      color = "warning";
    }
    return (
      <div>
        <Tag color={color} bordered={false}>
          <Tooltip title={formatDate(dayjs().add(daysLeft, "day").toDate())}>
            <>{daysLeft} days left</>
          </Tooltip>
        </Tag>
      </div>
    );
  }

  return <></>;
};

export const RequestTable = ({ ...props }: BoxProps): JSX.Element => {
  const { plus: hasPlus } = useFeatures();
  const [fuzzySearchTerm, setFuzzySearchTerm] = useQueryState(
    "search",
    parseAsString.withDefault("").withOptions({ throttleMs: 100 }),
  );
  const filters = useSelector(selectPrivacyRequestFilters);
  const token = useSelector(selectToken);
  const toast = useToast();
  const router = useRouter();
  const dispatch = useDispatch();

  const { pageIndex, pageSize, resetPagination } = useAntPaginationContext();

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
      downloadReport(filters);
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
      resetPagination();
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
    columns: useMemo(() => getRequestTableColumns(hasPlus), [hasPlus]),
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
              itemLayout="vertical"
              dataSource={requests}
              renderItem={(item) => {
                return (
                  <List.Item>
                    <Row justify="space-between" gutter={[20, 20]} wrap>
                      <Col sm={24} md={24} lg={20}>
                        <Row wrap>
                          <Col xs={24} sm={18}>
                            <Flex vertical gap={8}>
                              <Space wrap>
                                <Typography.Title
                                  level={3}
                                  copyable={{
                                    text: item.id,
                                    tooltips: "Copy Request Id",
                                  }}
                                >
                                  {item.policy.name}
                                </Typography.Title>
                                <RequestStatusBadge status={item.status} />
                              </Space>
                              <Flex gap={8} wrap>
                                <Tag>{item.source}</Tag>
                                {getActionTypesFromRules(item.policy.rules)
                                  .map((actionType) =>
                                    SubjectRequestActionTypeMap.get(actionType),
                                  )
                                  .map((actionType) => (
                                    <Tag>{actionType}</Tag>
                                  ))}
                              </Flex>
                            </Flex>
                          </Col>
                          <Col xs={24} sm={6}>
                            <Flex justify="end" vertical align="end">
                              <div>
                                <Tag bordered={false}>
                                  <Tooltip title={formatDate(item.created_at)}>
                                    <Typography.Text>
                                      {sentenceCase(
                                        formatDistance(
                                          new Date(item.created_at),
                                          new Date(),
                                          {
                                            addSuffix: true,
                                          },
                                        ),
                                      )}
                                    </Typography.Text>
                                  </Tooltip>
                                </Tag>
                              </div>

                              <DaysLeft
                                daysLeft={item.days_left}
                                status={item.status}
                                timeframe={item.policy.execution_timeframe}
                              />
                            </Flex>
                          </Col>
                        </Row>
                        <Row gutter={[20, 20]}>
                          <Col span={12} xs={24} sm={24}>
                            <Descriptions
                              layout="vertical"
                              style={{ paddingTop: 8 }}
                            >
                              {Object.values(item.identity)
                                .concat(
                                  Object.values(
                                    item.custom_privacy_request_fields ?? {},
                                  ),
                                )
                                .map(({ label, value }) =>
                                  value ? (
                                    <Descriptions.Item
                                      label={label}
                                      style={{ paddingBottom: 0 }}
                                    >
                                      <Typography.Text copyable>
                                        {value}
                                      </Typography.Text>
                                    </Descriptions.Item>
                                  ) : null,
                                )}
                            </Descriptions>
                          </Col>
                        </Row>
                      </Col>
                      <Col sm={24} md={24} lg={4}>
                        <Card size="small" style={{ height: "100%" }}>
                          <Space.Compact
                            direction="vertical"
                            style={{ width: "100%" }}
                          >
                            <Link
                              href={`/privacy-requests/${item.id}`}
                              passHref
                              legacyBehavior
                            >
                              <Button icon={<Icons.View />}>View</Button>
                            </Link>

                            {item.status === PrivacyRequestStatus.PENDING ? (
                              <>
                                <Button icon={<Icons.Checkmark />}>
                                  Approve
                                </Button>
                                <Button icon={<Icons.Close />}>Deny</Button>
                                <Button icon={<Icons.TrashCan />}>
                                  Delete
                                </Button>
                              </>
                            ) : null}
                            {item.status ===
                            PrivacyRequestStatus.REQUIRES_INPUT ? (
                              <Button icon={<Icons.ListChecked />}>
                                Tasks
                              </Button>
                            ) : null}
                            {item.status ===
                            PrivacyRequestStatus.REQUIRES_MANUAL_FINALIZATION ? (
                              <Button>Finalize Erasure</Button>
                            ) : null}
                          </Space.Compact>
                        </Card>
                      </Col>
                    </Row>
                  </List.Item>
                );
              }}
              bordered
            />
          </Spin>
          <AntPaginator total={totalRows ?? 0} align="end" />
        </Flex>
      )}
    </Box>
  );
};
