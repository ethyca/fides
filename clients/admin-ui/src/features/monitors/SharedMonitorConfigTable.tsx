import { AntButton, AntFlex, AntSpin, AntTable } from "fidesui";
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

  const { data, isLoading, isFetching } = useGetSharedMonitorConfigsQuery({
    page: pageIndex,
    size: pageSize,
  });

  const columns = useSharedMonitorConfigColumns();

  const showSpinner = isLoading || isFetching;

  if (showSpinner) {
    return (
      <AntSpin
        size="large"
        className="flex h-full items-center justify-center"
      />
    );
  }

  return (
    <>
      <CustomTypography.Title level={2}>
        Shared monitor configurations
      </CustomTypography.Title>
      <CustomTypography.Paragraph className="mt-2">
        Shared monitor configurations can be applied to monitors to customize
        classification.
      </CustomTypography.Paragraph>
      <AntTable
        columns={columns}
        dataSource={data?.items}
        size="small"
        pagination={false}
        onRow={(row) => ({
          onClick: () => {
            onRowClick(row);
          },
          className: "cursor-pointer",
        })}
      />
      <AntFlex justify="space-between">
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
        <AntButton type="primary" onClick={onNewClick} className="mt-2">
          Create new
        </AntButton>
      </AntFlex>
    </>
  );
};

export default SharedMonitorConfigTable;
