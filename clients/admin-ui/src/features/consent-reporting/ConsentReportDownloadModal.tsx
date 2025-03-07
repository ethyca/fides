import { Dayjs } from "dayjs";
import {
  AntButton as Button,
  AntTypography as Typography,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
} from "fidesui";

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
  const handleDownloadClicked = () => {
    downloadReport({
      startDate,
      endDate,
    });
  };

  return (
    <Modal
      id="consent-report-download-modal"
      isOpen={isOpen}
      onClose={onClose}
      size="xl"
      returnFocusOnClose={false}
      isCentered
    >
      <ModalOverlay />
      <ModalContent>
        <ModalCloseButton />
        <ModalHeader pb={0}>Consent report download</ModalHeader>
        <ModalBody>
          <Typography.Paragraph>
            Download a CSV containing a report of consent preferences made by
            users on your sites. Depending on the number of records in the date
            range you select, it may take several minutes to prepare the file
            after you click &quot;Download report&quot;.
          </Typography.Paragraph>

          <Button
            loading={isDownloadingReport}
            onClick={handleDownloadClicked}
            data-testid="download-report-btn"
            type="primary"
            className="mb-2"
          >
            Download report
          </Button>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};
export default ConsentReportDownloadModal;
