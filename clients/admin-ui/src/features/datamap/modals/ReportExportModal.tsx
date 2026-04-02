import { Button, Flex, Form, Modal, Paragraph, Select } from "fidesui";
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
        <Flex gap="small" justify="flex-end">
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
      <Flex vertical gap="small">
        <Paragraph>
          Export your data map report using the options below. Depending on the
          number of rows, the file may take a few minutes to process.
        </Paragraph>
        <Form.Item label="Choose Format">
          <Select
            aria-label="Choose Format"
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
        </Form.Item>
      </Flex>
    </Modal>
  );
};

export default ReportExportModal;
