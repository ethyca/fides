import { Dayjs } from "dayjs";
import { Button, Flex, Modal, Typography } from "fidesui";

import useConsentReportingDownload from "./hooks/useConsentReportingDownload";

interface ConsentReportDownloadModalProps {
  isOpen: boolean;
  onClose: () => void;
  startDate: Dayjs | null;
  endDate: Dayjs | null;
}

const ConsentReportDownloadModal = ({
  isOpen,
  onClose,
  startDate,
  endDate,
}: ConsentReportDownloadModalProps) => {
  const { downloadReport, isDownloadingReport } = useConsentReportingDownload();
  const handleDownloadClicked = async () => {
    await downloadReport({
      startDate,
      endDate,
    });
    onClose();
  };

  return (
    <Modal
      open={isOpen}
      onCancel={onClose}
      centered
      destroyOnHidden
      title="Download consent report"
      footer={null}
    >
      <Typography.Paragraph>
        The downloaded CSV may differ from the UI in Fides, including column
        order and naming.
      </Typography.Paragraph>
      <Typography.Paragraph>
        For large datasets, file generation may take a few minutes after
        selecting &quot;Download&quot;.
      </Typography.Paragraph>

      <Flex justify="flex-end">
        <Button
          loading={isDownloadingReport}
          onClick={handleDownloadClicked}
          data-testid="download-report-btn"
          type="primary"
          className="mb-2"
        >
          Download
        </Button>
      </Flex>
    </Modal>
  );
};
export default ConsentReportDownloadModal;
