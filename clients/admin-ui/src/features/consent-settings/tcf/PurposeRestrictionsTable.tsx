import { getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { AntButton as Button, AntFlex as Flex, Spacer, Text } from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

import { FidesTableV2, TableActionBar } from "~/features/common/table/v2";
import { TCFRestrictionType, TCFVendorRestriction } from "~/types/api";

import { PurposeRestrictionFormModal } from "./PurposeRestrictionFormModal";
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

  // Get purpose ID from the URL
  const purposeId = router.query.purpose_id
    ? parseInt(router.query.purpose_id as string, 10)
    : undefined;

  // TASK: Fetch data from API
  const data: PurposeRestriction[] = [
    {
      restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
      vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
      vendor_ids: ["123", "456", "10-100"],
      purpose_id: purposeId,
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
        existingRestrictions={data}
        purposeId={purposeId}
      />
    </Flex>
  );
};
