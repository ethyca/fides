import { Box, HStack, Text, WarningTwoIcon } from "@fidesui/react";
import { ReactNode } from "react";

type Props = {
  title: string;
  description: string | ReactNode;
  button?: ReactNode;
};

const EmptyTableState = ({ title, description, button }: Props) => (
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
      <Text fontWeight="bold" fontSize="sm" mb={1}>
        {title}
      </Text>

      <Text fontSize="sm" color="gray.600" lineHeight="5">
        {description}
      </Text>
    </Box>
    {button}
  </HStack>
);

export default EmptyTableState;
