import {
  CloseButton,
  HStack,
  Spinner,
  Stack,
  Text,
  useDisclosure,
} from "@fidesui/react";

import WarningModal from "~/features/common/modals/WarningModal";

const warningModalMessage = (
  <>
    <Text color="gray.500" mb={3}>
      Warning, you are about to cancel the scan!
    </Text>
    <Text color="gray.500" mb={3}>
      If you cancel scanning, the scanner will stop and no systems will be
      returned.
    </Text>
    <Text color="gray.500" mb={3}>
      Are you sure you want to cancel?
    </Text>
  </>
);

interface Props {
  title: string;
  onClose: () => void;
}
const ScannerLoading = ({ title, onClose }: Props) => {
  const {
    isOpen: isWarningOpen,
    onOpen: onWarningOpen,
    onClose: onWarningClose,
  } = useDisclosure();

  return (
    <>
      <Stack spacing={8} data-testid="scanner-loading">
        <HStack>
          <Text
            alignItems="center"
            as="b"
            color="gray.900"
            display="flex"
            fontSize="xl"
          >
            {title}
          </Text>
          <CloseButton
            data-testid="close-scan-in-progress"
            display="inline-block"
            onClick={onWarningOpen}
          />
        </HStack>

        <Stack alignItems="center">
          <Spinner
            thickness="4px"
            speed="0.65s"
            emptyColor="gray.200"
            color="green.300"
            size="xl"
          />
        </Stack>
      </Stack>
      <WarningModal
        isOpen={isWarningOpen}
        onClose={onWarningClose}
        handleConfirm={onClose}
        title="Cancel Scan!"
        message={warningModalMessage}
        confirmButtonText="Yes, Cancel"
        cancelButtonText="No, Continue Scanning"
      />
    </>
  );
};

export default ScannerLoading;
