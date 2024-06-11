/* eslint-disable react/no-unstable-nested-components */

import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Button, Spacer, Spinner, Text, useDisclosure } from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { MonitorIcon } from "~/features/common/Icon/MonitorIcon";
import EmptyTableNotice from "~/features/common/table/EmptyTableNotice";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GroupCountBadgeCell,
  PaginationBar,
  TableActionBar,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { useGetMonitorsByIntegrationQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import ConfigureMonitorModal from "~/features/integrations/configure-monitor/ConfigureMonitorModal";
import MonitorConfigActionsCell from "~/features/integrations/configure-monitor/MonitorConfigActionsCell";
import { ConnectionConfigurationResponse, MonitorConfig } from "~/types/api";

const EMPTY_RESPONSE = {
  items: [] as MonitorConfig[],
  total: 0,
  page: 1,
  size: 50,
  pages: 0,
};

const columnHelper = createColumnHelper<MonitorConfig>();

const NoMonitors = ({ onAddClick }: { onAddClick: () => void }) => (
  <EmptyTableNotice
    title="No monitors"
    description='You have not configured any data discovery monitors. Click "Add monitor" to configure data discovery now.'
    button={
      <Button onClick={onAddClick} colorScheme="primary">
        Add monitor
      </Button>
    }
  />
);

const MonitorConfigTab = ({
  integration,
}: {
  integration: ConnectionConfigurationResponse;
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
  const [monitorToEdit, setMonitorToEdit] = useState<MonitorConfig | undefined>(
    undefined
  );
  const [formStep, setFormStep] = useState(0);

  const handleEditMonitor = (monitor: MonitorConfig) => {
    setMonitorToEdit(monitor);
    modal.onOpen();
  };

  const handleCloseModal = () => {
    setMonitorToEdit(undefined);
    setFormStep(0);
    modal.onClose();
  };

  const handleAdvanceForm = (monitor: MonitorConfig) => {
    setMonitorToEdit(monitor);
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
              isDisplayAll
            />
          ),
        header: (props) => <DefaultHeaderCell value="Location" {...props} />,
      }),
      columnHelper.display({
        id: "action",
        cell: (props) => (
          <MonitorConfigActionsCell
            onEditClick={() => handleEditMonitor(props.row.original)}
          />
        ),
        header: "Actions",
        meta: { disableRowClick: true },
        maxSize: 50,
      }),
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const tableInstance = useReactTable<MonitorConfig>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    getRowId: (row) => row.name,
    manualPagination: true,
    data: monitors,
    columns,
  });

  if (isLoading) {
    return <Spinner />;
  }

  return (
    <>
      <Text maxW="720px" mb={6} fontSize="sm">
        Data discovery monitors observe configured systems for data model
        changes to proactively discover and classify data risks. You can create
        multiple monitors to observe part or all of a project, dataset, table or
        API for changes and assign these to different data stewards.
      </Text>
      <TableActionBar>
        <Spacer />
        <Button
          onClick={modal.onOpen}
          size="xs"
          variant="outline"
          rightIcon={<MonitorIcon />}
          data-testid="add-monitor-btn"
        >
          Add monitor
        </Button>
        <ConfigureMonitorModal
          isOpen={modal.isOpen}
          onClose={handleCloseModal}
          formStep={formStep}
          onAdvance={handleAdvanceForm}
          monitor={monitorToEdit}
        />
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        onRowClick={handleEditMonitor}
        emptyTableNotice={<NoMonitors onAddClick={modal.onOpen} />}
      />
      <PaginationBar
        totalRows={totalRows}
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
