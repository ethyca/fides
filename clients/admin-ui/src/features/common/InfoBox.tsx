import { Flex, Heading, HStack, Text, WarningTwoIcon } from "fidesui";
import { ReactNode } from "react";

const InfoBox = ({
  title,
  text,
  button,
}: {
  title?: string;
  text: string | ReactNode;
  button?: ReactNode;
}) => (
  <HStack
    backgroundColor="gray.50"
    border="1px solid"
    borderColor="blue.400"
    borderRadius="md"
    justifyContent="space-between"
    py={4}
    px={6}
    data-testid="info-box"
  >
    <WarningTwoIcon alignSelf="start" color="blue.400" mt={0.5} />
    <Flex direction="column" gap={2}>
      <Heading fontSize="md">{title}</Heading>
      <Text fontSize="sm" color="gray.600" lineHeight="5">
        {text}
      </Text>
      <HStack>{button}</HStack>
    </Flex>
  </HStack>
);

export default InfoBox;
