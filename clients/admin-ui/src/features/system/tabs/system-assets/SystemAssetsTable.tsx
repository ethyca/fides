import {
  getCoreRowModel,
  RowSelectionState,
  useReactTable,
} from "@tanstack/react-table";
import {
  AntButton,
  AntEmpty as Empty,
  ConfirmationModal,
  Icons,
  Spacer,
  useDisclosure,
  useToast,
} from "fidesui";
import { useEffect, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import {
  FidesTableV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { SearchInput } from "~/features/data-discovery-and-detection/SearchInput";
import {
  useDeleteSystemAssetsMutation,
  useGetSystemAssetsQuery,
} from "~/features/system/system-assets.slice";
import AddEditAssetModal from "~/features/system/tabs/system-assets/AddEditAssetModal";
import useSystemAssetColumns from "~/features/system/tabs/system-assets/useSystemAssetColumns";
import { Asset, SystemResponse } from "~/types/api";
import { isErrorResult } from "~/types/errors";

const SystemAssetsTable = ({ system }: { system: SystemResponse }) => {
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
    resetPageIndexToDefault,
  } = useServerSidePagination();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedAsset, setSelectedAsset] = useState<Asset | undefined>(
    undefined,
  );
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});

  const [deleteAssets] = useDeleteSystemAssetsMutation();

  const toast = useToast();

  const { data, isLoading, isFetching } = useGetSystemAssetsQuery({
    fides_key: system.fides_key,
    search: searchQuery,
    page: pageIndex,
    size: pageSize,
  });

  const {
    isOpen: addEditModalIsOpen,
    onClose: onCloseAddEditModal,
    onOpen: onOpenAddEditModal,
  } = useDisclosure();

  const {
    isOpen: isDeleteModalOpen,
    onClose: onCloseDeleteModal,
    onOpen: onOpenDeleteModal,
  } = useDisclosure();

  useEffect(() => {
    resetPageIndexToDefault();
  }, [searchQuery, resetPageIndexToDefault]);

  useEffect(() => {
    setTotalPages(data?.pages);
  }, [data, setTotalPages]);

  const handleEditAsset = (a: Asset) => {
    setSelectedAsset(a);
    onOpenAddEditModal();
  };

  const handleCloseModal = () => {
    setSelectedAsset(undefined);
    onCloseAddEditModal();
  };

  const columns = useSystemAssetColumns({
    systemKey: system.fides_key,
    onEditClick: handleEditAsset,
  });

  const tableInstance = useReactTable({
    getCoreRowModel: getCoreRowModel(),
    columns,
    manualPagination: true,
    data: data?.items || [],
    columnResizeMode: "onChange",
    onRowSelectionChange: setRowSelection,
    state: {
      rowSelection,
    },
  });

  const selectedRows = tableInstance.getSelectedRowModel().rows;
  const selectedAssetIds = selectedRows.map((row) => row.original.id);

  const handleBulkDelete = async () => {
    const result = await deleteAssets({
      systemKey: system.fides_key,
      asset_ids: selectedAssetIds,
    });
    if (isErrorResult(result)) {
      toast(
        errorToastParams(
          getErrorMessage(
            result.error,
            "A problem occurred removing these assets. Please try again.",
          ),
        ),
      );
    } else {
      tableInstance.resetRowSelection();
      toast(successToastParams("Assets removed successfully"));
    }
    onCloseDeleteModal();
  };

  if (!system) {
    return null;
  }

  if (isLoading) {
    return <TableSkeletonLoader rowHeight={36} numRows={36} />;
  }

  return (
    <>
      <TableActionBar>
        <SearchInput value={searchQuery} onChange={setSearchQuery} />
        <Spacer />
        <AntButton
          icon={<Icons.Add />}
          iconPosition="end"
          onClick={onOpenAddEditModal}
          data-testid="add-asset-btn"
        >
          Add asset
        </AntButton>
        <AddEditAssetModal
          isOpen={addEditModalIsOpen}
          onClose={handleCloseModal}
          systemKey={system.fides_key}
          asset={selectedAsset}
        />
        <AntButton
          icon={<Icons.TrashCan />}
          iconPosition="end"
          onClick={onOpenDeleteModal}
          disabled={!selectedAssetIds.length}
          data-testid="bulk-delete-btn"
        >
          Remove
        </AntButton>
        <ConfirmationModal
          isOpen={isDeleteModalOpen}
          onClose={onCloseDeleteModal}
          onConfirm={handleBulkDelete}
          title="Remove assets"
          message="Are you sure you want to remove the selected assets? This action cannot be undone and may impact consent automation."
          isCentered
        />
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        emptyTableNotice={
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="No assets found"
            data-testid="empty-state"
          />
        }
      />
      <PaginationBar
        totalRows={data?.total || 0}
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

export default SystemAssetsTable;
