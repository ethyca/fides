import {
  AntButton as Button,
  AntFlex as Flex,
  AntSpin as Spin,
  AntTable as Table,
} from "fidesui";
import { CustomTypography } from "fidesui/src/hoc";

import {
  PaginationBar,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { useGetSharedMonitorConfigsQuery } from "~/features/monitors/shared-monitor-config.slice";
import useSharedMonitorConfigColumns from "~/features/monitors/useSharedMonitorConfigColumns";
import { SharedMonitorConfig } from "~/types/api";

const SharedMonitorConfigTable = ({
  onNewClick,
  onRowClick,
}: {
  onNewClick: () => void;
  onRowClick: (row: SharedMonitorConfig) => void;
}) => {
  const {
    onPreviousPageClick,
    isPreviousPageDisabled,
    onNextPageClick,
    isNextPageDisabled,
    pageSize,
    setPageSize,
    PAGE_SIZES,
    startRange,
    endRange,
    pageIndex,
  } = useServerSidePagination();

  const {
    // data,
    isLoading,
    isFetching,
  } = useGetSharedMonitorConfigsQuery({
    page: pageIndex,
    size: pageSize,
  });

  const data = {
    items: [],
    total: 0,
  };

  const columns = useSharedMonitorConfigColumns({ onEditClick: onRowClick });

  const showSpinner = isLoading || isFetching;

  if (showSpinner) {
    return (
      <Spin size="large" className="flex h-full items-center justify-center" />
    );
  }

  return (
    <>
      <CustomTypography.Title level={2}>
        Shared monitor configurations
      </CustomTypography.Title>
      <CustomTypography.Paragraph className="mt-4">
        Shared monitor configurations can be applied to monitors to customize
        classification.
      </CustomTypography.Paragraph>
      <Flex className="absolute right-16 top-4">
        <Button
          type="primary"
          onClick={onNewClick}
          data-testid="create-new-btn"
        >
          Create new
        </Button>
      </Flex>
      <Table
        columns={columns}
        dataSource={data?.items}
        size="small"
        pagination={false}
        // @ts-ignore -- TS doesn't like the data-testid prop on rows
        onRow={(row) => ({
          "data-testid": `config-${row.id}`,
        })}
        locale={{
          emptyText: (
            <CustomTypography.Paragraph className="py-8">
              No shared monitor configs found
            </CustomTypography.Paragraph>
          ),
        }}
        className="mt-6"
      />
      <Flex justify="space-between" className="mt-4">
        <PaginationBar
          totalRows={data?.total || 0}
          pageSizes={PAGE_SIZES}
          setPageSize={setPageSize}
          onPreviousPageClick={onPreviousPageClick}
          isPreviousPageDisabled={isPreviousPageDisabled}
          onNextPageClick={onNextPageClick}
          isNextPageDisabled={isNextPageDisabled}
          startRange={startRange}
          endRange={endRange}
        />
      </Flex>
    </>
  );
};

export default SharedMonitorConfigTable;
