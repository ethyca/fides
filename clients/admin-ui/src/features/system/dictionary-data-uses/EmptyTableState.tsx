import {
  Box,
  Button,
  Flex,
  HStack,
  Stack,
  Text,
  WarningTwoIcon,
} from "@fidesui/react";
import { ReactNode } from "react";

type Props = {
  title: string;
  description: string | ReactNode;
  handleAdd: () => void;
  handleDictSuggestion: () => void;
};

const EmptyTableState = ({
  title,
  description,
  handleAdd,
  handleDictSuggestion,
}: Props) => (
  <Stack
    backgroundColor="gray.50"
    border="1px solid"
    borderColor="blue.400"
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
      </Box>
    </HStack>
    <HStack>
      <Button
        size="xs"
        variant="outline"
        fontWeight="semibold"
        data-testid="add-btn"
        onClick={handleAdd}
      >
        Add data use
      </Button>
    </HStack>
  </Stack>
);

export default EmptyTableState;
