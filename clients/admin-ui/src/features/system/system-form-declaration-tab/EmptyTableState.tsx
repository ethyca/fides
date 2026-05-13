import {
  ChakraBox as Box,
  Button,
  ChakraHStack as HStack,
  Icons,
  ChakraStack as Stack,
  ChakraText as Text,
} from "fidesui";
import type { ReactNode } from "react";

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
      <Box as="span" alignSelf="start" color="blue.400" mt={0.5}>
        <Icons.WarningAltFilled size={16} />
      </Box>

      <Box>
        <Text fontWeight="bold" fontSize="sm" mb={1}>
          {title}
        </Text>

        <Text fontSize="sm" color="gray.800" lineHeight="5">
          {description}
        </Text>
        <HStack mt={4}>
          <Button
            size="small"
            type="primary"
            data-testid="add-btn"
            onClick={handleAdd}
            icon={<Icons.Add size={16} />}
            iconPlacement="end"
          >
            Add data use
          </Button>
        </HStack>
      </Box>
    </HStack>
  </Stack>
);

export default EmptyTableState;
