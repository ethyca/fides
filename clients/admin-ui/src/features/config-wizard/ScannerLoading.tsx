import {
  ChakraCloseButton as CloseButton,
  ChakraHStack as HStack,
  ChakraStack as Stack,
  ChakraText as Text,
  Spin,
  useModal,
} from "fidesui";

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
  const modal = useModal();

  const openCancelWarning = () => {
    modal.confirm({
      title: "Cancel Scan!",
      content: warningModalMessage,
      okText: "Yes, Cancel",
      cancelText: "No, Continue Scanning",
      centered: true,
      onOk: onClose,
    });
  };

  return (
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
          onClick={openCancelWarning}
        />
      </HStack>

      <Stack alignItems="center">
        <Spin size="large" />
      </Stack>
    </Stack>
  );
};

export default ScannerLoading;
