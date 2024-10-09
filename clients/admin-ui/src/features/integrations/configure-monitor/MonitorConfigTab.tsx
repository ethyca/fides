/* eslint-disable react/no-unstable-nested-components */

import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  AntButton as Button,
  Spacer,
  Text,
  useDisclosure,
  VStack,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

import FidesSpinner from "~/features/common/FidesSpinner";
import { MonitorIcon } from "~/features/common/Icon/MonitorIcon";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GroupCountBadgeCell,
  PaginationBar,
  TableActionBar,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { RelativeTimestampCell } from "~/features/common/table/v2/cells";
import { useGetMonitorsByIntegrationQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import ConfigureMonitorModal from "~/features/integrations/configure-monitor/ConfigureMonitorModal";
import MonitorConfigActionsCell from "~/features/integrations/configure-monitor/MonitorConfigActionsCell";
import { MonitorConfigEnableCell } from "~/features/integrations/configure-monitor/MonitorConfigEnableCell";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  MonitorConfig,
} from "~/types/api";

const EMPTY_RESPONSE = {
  items: [] as MonitorConfig[],
  total: 0,
  page: 1,
  size: 50,
  pages: 0,
};

const columnHelper = createColumnHelper<MonitorConfig>();

const EmptyTableNotice = ({ onAddClick }: { onAddClick: () => void }) => (
  <VStack
    mt={6}
    p={10}
    spacing={4}
    borderRadius="base"
    maxW="70%"
    data-testid="no-results-notice"
    alignSelf="center"
    margin="auto"
  >
    <VStack>
      <Text fontSize="md" fontWeight="600">
        No monitors
      </Text>
      <Text fontSize="sm">
        You have not configured any data discovery monitors. Click &quot;Add
        monitor&quot; to configure data discovery now.
      </Text>
      <Button onClick={onAddClick} type="primary">
        Add monitor
      </Button>
    </VStack>
  </VStack>
);

const MonitorConfigTab = ({
  integration,
  integrationOption,
}: {
  integration: ConnectionConfigurationResponse;
  integrationOption?: ConnectionSystemTypeMap;
}) => {
  const {
    PAGE_SIZES,
    pageSize,
    setPageSize,
    onPreviousPageClick,
    isPreviousPageDisabled,
    onNextPageClick,
    isNextPageDisabled,
    startRange,
    endRange,
    pageIndex,
    setTotalPages,
  } = useServerSidePagination();

  const {
    isLoading,
    isFetching,
    data: monitorResult,
  } = useGetMonitorsByIntegrationQuery({
    page: pageIndex,
    size: pageSize,
    connection_config_key: integration.key,
  });

  const modal = useDisclosure();
  const [workingMonitor, setWorkingMonitor] = useState<
    MonitorConfig | undefined
  >(undefined);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [formStep, setFormStep] = useState(0);

  const handleEditMonitor = (monitor: MonitorConfig) => {
    setWorkingMonitor(monitor);
    setIsEditing(true);
    modal.onOpen();
  };

  const handleCloseModal = () => {
    setWorkingMonitor(undefined);
    setIsEditing(false);
    setFormStep(0);
    modal.onClose();
  };

  const handleAdvanceForm = (monitor: MonitorConfig) => {
    setWorkingMonitor(monitor);
    setFormStep(1);
  };

  const response = monitorResult ?? EMPTY_RESPONSE;

  const {
    items: monitors,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => response, [response]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const columns: ColumnDef<MonitorConfig, any>[] = useMemo(
    () => [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Name" {...props} />,
      }),
      columnHelper.accessor((row) => row.databases, {
        id: "projects",
        cell: (props) =>
          props.getValue().length === 0 ? (
            <DefaultCell value="All projects" />
          ) : (
            <GroupCountBadgeCell
              suffix="Projects"
              value={props.getValue()}
              {...props}
              cellState={{ isExpanded: true }}
            />
          ),
        header: (props) => <DefaultHeaderCell value="Scope" {...props} />,
      }),
      columnHelper.accessor((row) => row.execution_frequency, {
        id: "frequency",
        cell: (props) => (
          <DefaultCell value={props.getValue() ?? "Not scheduled"} />
        ),
        header: (props) => (
          <DefaultHeaderCell value="Scan frequency" {...props} />
        ),
      }),
      columnHelper.accessor((row) => row.last_monitored, {
        id: "last_monitored",
        cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Last scan" {...props} />,
      }),
      columnHelper.accessor((row) => row.enabled, {
        id: "status",
        cell: MonitorConfigEnableCell,
        header: (props) => <DefaultHeaderCell value="Status" {...props} />,
        size: 0,
        meta: { disableRowClick: true },
      }),
      columnHelper.display({
        id: "action",
        cell: (props) => (
          <MonitorConfigActionsCell
            onEditClick={() => handleEditMonitor(props.row.original)}
            monitorId={props.row.original.key!}
          />
        ),
        header: "Actions",
        meta: { disableRowClick: true },
      }),
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  const tableInstance = useReactTable<MonitorConfig>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    getRowId: (row) => row.name,
    manualPagination: true,
    data: monitors,
    columns,
    columnResizeMode: "onChange",
  });

  if (isLoading) {
    return <FidesSpinner />;
  }

  return (
    <>
      <Text maxW="720px" mb={6} fontSize="sm">
        A data discovery monitor observes configured systems for data model
        changes to proactively discover and classify data risks. Monitors can
        observe part or all of a project, dataset, table, or API for changes and
        each can be assigned to a different data steward.
      </Text>
      <TableActionBar>
        <Spacer />
        <Button
          onClick={modal.onOpen}
          size="small"
          icon={<MonitorIcon />}
          iconPosition="end"
          data-testid="add-monitor-btn"
        >
          Add monitor
        </Button>
        <ConfigureMonitorModal
          isOpen={modal.isOpen}
          onClose={handleCloseModal}
          formStep={formStep}
          onAdvance={handleAdvanceForm}
          monitor={workingMonitor}
          isEditing={isEditing}
          integration={integration}
          integrationOption={integrationOption!}
        />
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        onRowClick={handleEditMonitor}
        emptyTableNotice={<EmptyTableNotice onAddClick={modal.onOpen} />}
      />
      <PaginationBar
        totalRows={totalRows || 0}
        pageSizes={PAGE_SIZES}
        setPageSize={setPageSize}
        onPreviousPageClick={onPreviousPageClick}
        isPreviousPageDisabled={isPreviousPageDisabled || isFetching}
        onNextPageClick={onNextPageClick}
        isNextPageDisabled={isNextPageDisabled || isFetching}
        startRange={startRange}
        endRange={endRange}
      />
    </>
  );
};

export default MonitorConfigTab;
