/* eslint-disable react/no-unstable-nested-components */
import { getCoreRowModel, useReactTable } from "@tanstack/react-table";
import {
  AntEmpty as Empty,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
} from "fidesui";

import { PreferencesSaved } from "~/types/api";

import { FidesTableV2 } from "../common/table/v2";
import useTcfConsentColumns, {
  TcfDetailRow,
} from "./hooks/useTcfConsentColumns";

interface ConsentTcfDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  tcfPreferences?: PreferencesSaved;
}

const ConsentTcfDetailModal = ({
  isOpen,
  onClose,
  tcfPreferences,
}: ConsentTcfDetailModalProps) => {
  const { tcfColumns, mapTcfPreferencesToRowColumns } = useTcfConsentColumns();
  const tcfData = mapTcfPreferencesToRowColumns(tcfPreferences);

  const tableInstance = useReactTable<TcfDetailRow>({
    getCoreRowModel: getCoreRowModel(),
    data: tcfData || [],
    columns: tcfColumns,
    getRowId: (row) => `${row.key}-${row.id}`,
    manualPagination: true,
  });

  return (
    <Modal
      id="consent-lookup-modal"
      isOpen={isOpen}
      onClose={onClose}
      size="4xl"
      returnFocusOnClose={false}
      isCentered
    >
      <ModalOverlay />
      <ModalContent>
        <ModalCloseButton />
        <ModalHeader pb={2}>TCF Consent Details</ModalHeader>
        <ModalBody>
          <div className="mb-4">
            <FidesTableV2<TcfDetailRow>
              tableInstance={tableInstance}
              emptyTableNotice={
                <Empty
                  description=" No data found"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  imageStyle={{ marginBottom: 15 }}
                />
              }
            />
          </div>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};
export default ConsentTcfDetailModal;
