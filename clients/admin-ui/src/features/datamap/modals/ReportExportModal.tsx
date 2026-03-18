import {
  Button,
  ChakraFlex as Flex,
  ChakraFormControl as FormControl,
  ChakraFormLabel as FormLabel,
  ChakraText as Text,
  Modal,
  Select,
} from "fidesui";
import { useState } from "react";

import { ExportFormat } from "~/features/datamap/constants";

interface ReportExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (downloadType: ExportFormat) => void;
  isLoading?: boolean;
}

const ReportExportModal = ({
  isOpen,
  onClose,
  onConfirm,
  isLoading,
}: ReportExportModalProps): JSX.Element => {
  const [downloadType, setDownloadType] = useState<ExportFormat>(
    ExportFormat.csv,
  );

  return (
    <Modal
      title="Export report"
      open={isOpen}
      onCancel={onClose}
      centered
      destroyOnClose
      data-testid="export-modal"
      footer={
        <Flex gap={12} justify="flex-end">
          <Button onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            type="primary"
            onClick={() => onConfirm(downloadType)}
            loading={isLoading}
          >
            Download
          </Button>
        </Flex>
      }
    >
      <Flex direction="column" gap={3} pb={3}>
        <Text textAlign="left">
          Export your data map report using the options below. Depending on the
          number of rows, the file may take a few minutes to process.
        </Text>
        <FormControl>
          <FormLabel htmlFor="format">Choose Format</FormLabel>
          {/* eslint-disable-next-line jsx-a11y/control-has-associated-label */}
          <Select
            id="format"
            value={downloadType}
            onChange={setDownloadType}
            data-testid="export-format-select"
            options={[
              { value: ExportFormat.csv, label: "CSV" },
              { value: ExportFormat.xlsx, label: "XLSX" },
            ]}
            className="w-full"
          />
        </FormControl>
      </Flex>
    </Modal>
  );
};

export default ReportExportModal;
