import { Box, HStack, Text, WarningTwoIcon } from "@fidesui/react";

const InfoBox = ({ text }: { text: string }) => (
  <HStack
    backgroundColor="gray.50"
    border="1px solid"
    borderColor="blue.400"
    borderRadius="md"
    justifyContent="space-between"
    py={4}
    px={6}
    data-testid="empty-state"
  >
    <WarningTwoIcon alignSelf="start" color="blue.400" mt={0.5} />
    <Box>
      <Text fontSize="sm" color="gray.600" lineHeight="5">
        {text}
      </Text>
    </Box>
  </HStack>
);

export default InfoBox;
