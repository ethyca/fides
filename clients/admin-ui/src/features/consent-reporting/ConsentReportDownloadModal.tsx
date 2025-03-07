import { Dayjs } from "dayjs";
import {
  AntButton as Button,
  AntFlex as Flex,
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
        <ModalHeader pb={2}>Download consent report</ModalHeader>
        <ModalBody>
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
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};
export default ConsentReportDownloadModal;
