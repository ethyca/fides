import { getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { AntButton as Button, AntFlex as Flex, Spacer, Text } from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

import {
  FidesTableV2,
  TableActionBar,
  TableSkeletonLoader,
} from "~/features/common/table/v2";
import { RangeEntry } from "~/types/api";

import { PurposeRestrictionFormModal } from "./PurposeRestrictionFormModal";
import { useGetPublisherRestrictionsQuery } from "./tcf-config.slice";
import { PurposeRestriction } from "./types";
import { usePurposeRestrictionTableColumns } from "./usePurposeRestrictionTableColumns";

const EmptyTableNotice = ({ onAdd }: { onAdd: () => void }) => (
  <Flex
    vertical
    align="center"
    className="mt-6 w-full gap-3 self-center whitespace-normal py-10"
    data-testid="empty-table-notice"
  >
    <Text fontSize="md" fontWeight="semibold">
      Add a restriction
    </Text>
    <Text fontSize="sm" className="max-w-[70%]">
      No restrictions have been added. By default, all vendors follow their
      declared legal basis unless a restriction is applied&mdash;add a
      restriction to override this behavior.
    </Text>
    <Button type="primary" onClick={onAdd}>
      Add +
    </Button>
  </Flex>
);

export const PurposeRestrictionsTable = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const columns = usePurposeRestrictionTableColumns();
  const router = useRouter();

  const purposeId = router.query.purpose_id
    ? parseInt(router.query.purpose_id as string, 10)
    : undefined;

  const configurationId = router.query.configuration_id as string;

  const { data: restrictionsData, isFetching } =
    useGetPublisherRestrictionsQuery(
      {
        configuration_id: configurationId,
        purpose_id: purposeId ?? 0,
      },
      { skip: !configurationId || !purposeId },
    );

  const transformedData: PurposeRestriction[] = (
    restrictionsData?.items || []
  ).map((item) => ({
    id: item.id,
    restriction_type: item.restriction_type,
    vendor_restriction: item.vendor_restriction,
    vendor_ids:
      item.range_entries?.map((range: RangeEntry) =>
        range.end_vendor_id
          ? `${range.start_vendor_id}-${range.end_vendor_id}`
          : range.start_vendor_id.toString(),
      ) || [],
    purpose_id: item.purpose_id,
  }));

  const table = useReactTable<PurposeRestriction>({
    getCoreRowModel: getCoreRowModel(),
    columns,
    data: transformedData,
    columnResizeMode: "onChange",
    manualPagination: true,
  });

  const handleOpenModal = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  return (
    <Flex vertical className="overflow-auto">
      <TableActionBar>
        <Spacer />
        <Button type="primary" onClick={handleOpenModal}>
          Add restriction +
        </Button>
      </TableActionBar>
      {isFetching ? (
        <TableSkeletonLoader rowHeight={36} numRows={3} />
      ) : (
        <FidesTableV2
          tableInstance={table}
          emptyTableNotice={<EmptyTableNotice onAdd={handleOpenModal} />}
        />
      )}
      <PurposeRestrictionFormModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        existingRestrictions={transformedData}
        purposeId={purposeId}
        configurationId={configurationId}
      />
    </Flex>
  );
};
