import {
  Button,
  Divider,
  Flex,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Text,
} from "@fidesui/react";
import { stringify } from "csv-stringify/sync";
import { saveAs } from "file-saver";
import React, { useContext, useRef } from "react";
import { utils, WorkBook, writeFileXLSX } from "xlsx";

import DatamapTableContext from "../datamap-table/DatamapTableContext";

export type ExportFileType = "xlsx" | "csv";

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ExportModal: React.FC<ExportModalProps> = ({ isOpen, onClose }) => {
  const initialRef = useRef(null);
  const { tableInstance } = useContext(DatamapTableContext);

  const generateExportFile = (
    data: {
      columns: string[] | null;
      rows: string[][] | null;
    } | null,
    fileType: ExportFileType
  ) => {
    if (!data || !data.columns || !data.rows) {
      return "";
    }
    const { columns, rows } = data;

    // If we are generating a CSV file, do that and return
    if (fileType === "csv") {
      return stringify([columns, ...rows]);
    }

    // Generate XLSX worksheet
    const worksheet = utils.aoa_to_sheet([columns, ...rows]);
    const workbook = utils.book_new();
    utils.book_append_sheet(workbook, worksheet, "Datamap");

    return workbook;
  };

  const generateROPAExportData = () => {
    const columns = tableInstance!.columns
      .filter((column) => column.isVisible)
      .map((column) => column.Header) as string[];

    const rows = tableInstance!.rows
      .map((row) => row.subRows)
      .flatMap((row) => row)
      .map((row) => row.cells.map((cell) => cell.value)) as string[][];
    return { columns, rows };
  };

  const triggerExportFileDownload = (
    file: string | WorkBook,
    fileType: ExportFileType
  ) => {
    const now = new Date().toISOString();
    const fileName = `report_[timestamp].${fileType}`.replace(
      "[timestamp]",
      now
    );
    if (typeof file === "string") {
      if (fileType === "csv") {
        const blob = new Blob([file], { type: "text/csv;charset=utf-8" });
        saveAs(blob, fileName);
      }
    } else {
      writeFileXLSX(file, fileName);
    }
  };

  const handleExportClick = async (fileType: ExportFileType) => {
    onClose();
    if (!tableInstance) {
      return;
    }
    const data = generateROPAExportData();
    const file = generateExportFile(data, fileType);
    triggerExportFileDownload(file, fileType);
  };

  return (
    <Modal
      initialFocusRef={initialRef}
      isCentered
      isOpen={isOpen}
      onClose={onClose}
      size="lg"
    >
      <ModalOverlay />
      <ModalContent minWidth="605px">
        <ModalHeader>
          <Flex flexDir="column" gap="16px">
            <Text>Export</Text>
            <Divider color="gray.200" />
          </Flex>
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody pb="8px" pt="8px">
          <Flex justifyContent="center" width="100%">
            <Text fontSize="sm" lineHeight="20px">
              To export the current view of the Data Map table, please select
              the appropriate format below. Your export will contain only the
              visible columns and rows.
            </Text>
          </Flex>
        </ModalBody>
        <ModalFooter>
          <Flex
            borderTop="1px solid"
            borderTopColor="gray.200"
            justifyContent="space-between"
            pt="24px"
            width="100%"
          >
            <Button
              colorScheme="primary"
              size="sm"
              mr={3}
              flexGrow={1}
              onClick={() => handleExportClick("xlsx")}
            >
              Export Excel (.xls)
            </Button>
            <Button
              colorScheme="primary"
              size="sm"
              flexGrow={1}
              onClick={() => handleExportClick("csv")}
            >
              Export CSV (.csv)
            </Button>
          </Flex>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default ExportModal;
