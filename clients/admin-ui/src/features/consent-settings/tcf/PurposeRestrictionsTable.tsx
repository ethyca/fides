import { getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { AntButton as Button, AntFlex as Flex, Spacer, Text } from "fidesui";
import { useState } from "react";

import { FidesTableV2, TableActionBar } from "~/features/common/table/v2";

import { RestrictionType, VendorRestriction } from "./constants";
import { PurposeRestrictionFormModal } from "./PurposeRestrictionFormModal";
import { usePurposeRestrictionTableColumns } from "./usePurposeRestrictionTableColumns";

export interface PurposeRestriction {
  restriction_type: RestrictionType;
  vendor_restriction: VendorRestriction;
  vendor_ids: string[];
}

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

  // TASK: Fetch data from API
  const data = [
    {
      restriction_type: RestrictionType.PURPOSE_RESTRICTION,
      vendor_restriction: VendorRestriction.RESTRICT_SPECIFIC,
      vendor_ids: ["123", "456", "10-100"],
    },
  ];

  const table = useReactTable<PurposeRestriction>({
    getCoreRowModel: getCoreRowModel(),
    columns,
    data: data || [],
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
      <FidesTableV2
        tableInstance={table}
        emptyTableNotice={<EmptyTableNotice onAdd={handleOpenModal} />}
      />
      <PurposeRestrictionFormModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </Flex>
  );
};
