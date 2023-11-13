import { AddIcon, WarningTwoIcon } from "@chakra-ui/icons";
import { Box, Button, HStack, Stack, Text } from "@fidesui/react";
import { ReactNode } from "react";

type Props = {
  title: string;
  description: string | ReactNode;
  handleAdd: () => void;
};

const EmptyTableState = ({ title, description, handleAdd }: Props) => (
  <Stack
    backgroundColor="gray.50"
    border="1px solid"
    borderColor="blue.500"
    borderRadius="md"
    justifyContent="space-between"
    py={4}
    px={6}
    data-testid="empty-state"
  >
    <HStack>
      <WarningTwoIcon alignSelf="start" color="blue.400" mt={0.5} />

      <Box>
        <Text fontWeight="bold" fontSize="sm" mb={1}>
          {title}
        </Text>

        <Text fontSize="sm" color="gray.600" lineHeight="5">
          {description}
        </Text>
        <HStack mt={4}>
          <Button
            size="xs"
            colorScheme="black"
            backgroundColor="primary.800"
            fontWeight="semibold"
            data-testid="add-btn"
            onClick={handleAdd}
            rightIcon={<AddIcon boxSize={2} />}
          >
            Add data use
          </Button>
        </HStack>
      </Box>
    </HStack>
  </Stack>
);

export default EmptyTableState;
