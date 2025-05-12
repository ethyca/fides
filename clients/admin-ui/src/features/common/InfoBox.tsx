import {
  CloseIcon,
  Flex,
  Heading,
  HStack,
  Text,
  WarningTwoIcon,
} from "fidesui";

const InfoBox = ({
  title,
  text,
  onClose,
}: {
  title?: string | React.ReactElement;
  text: string | React.ReactElement;
  onClose?: () => void;
}) => (
  <HStack
    backgroundColor="gray.50"
    border="1px solid"
    borderRadius="md"
    justifyContent="space-between"
    py={4}
    pr={6}
    pl={3}
    data-testid="empty-state"
    gap={2}
    position="relative"
  >
    {onClose && (
      <CloseIcon
        boxSize={5}
        position="absolute"
        right={3}
        top={3}
        zIndex={1}
        cursor="pointer"
        p={1}
        onClick={onClose}
      />
    )}
    <WarningTwoIcon alignSelf="start" color="minos" mt={0.5} flexGrow={0} />
    <Flex direction="column" gap={2} flexGrow={1}>
      <Heading fontSize="md">{title}</Heading>
      <Text fontSize="sm" color="gray.600" lineHeight="5">
        {text}
      </Text>
    </Flex>
  </HStack>
);

export default InfoBox;
