import { AddIcon, WarningTwoIcon } from "@chakra-ui/icons";
import { Box, Button, HStack, Stack, Text, Tooltip } from "@fidesui/react";
import { ReactNode, useMemo } from "react";

import { SparkleIcon } from "../../common/Icon/SparkleIcon";

type Props = {
  title: string;
  description: string | ReactNode;
  dictAvailable: boolean;
  handleAdd: () => void;
  handleDictSuggestion: () => void;
  vendorSelected: boolean;
};

const EmptyTableState = ({
  title,
  description,
  dictAvailable = false,
  handleAdd,
  handleDictSuggestion,
  vendorSelected,
}: Props) => {
  const dictDisabledTooltip = useMemo(
    () =>
      "You will need to select a vendor for this system before you can use the Fides dictionary. You can do this on System Information tab above.",
    []
  );

  return (
    <Stack
      backgroundColor="gray.50"
      border="1px solid"
      borderColor={dictAvailable ? "purple.400" : "blue.500"}
      borderRadius="md"
      justifyContent="space-between"
      py={4}
      px={6}
      data-testid="empty-state"
    >
      <HStack>
        {dictAvailable ? (
          <SparkleIcon alignSelf="start" color="purple.400" mt={0.5} />
        ) : (
          <WarningTwoIcon alignSelf="start" color="blue.400" mt={0.5} />
        )}

        <Box>
          <Text fontWeight="bold" fontSize="sm" mb={1}>
            {title}
          </Text>

          <Text fontSize="sm" color="gray.600" lineHeight="5">
            {description}
          </Text>
          <HStack mt={4}>
            {dictAvailable ? (
              <>
                <Tooltip
                  hasArrow
                  placement="top"
                  label={dictDisabledTooltip}
                  isDisabled={vendorSelected}
                >
                  <Button
                    size="xs"
                    colorScheme="purple"
                    fontWeight="semibold"
                    data-testid="dict-btn"
                    onClick={handleDictSuggestion}
                    rightIcon={<SparkleIcon />}
                    disabled={!vendorSelected}
                  >
                    Generate data uses automatically
                  </Button>
                </Tooltip>
                <Text size="sm">or</Text>
              </>
            ) : null}
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
};

export default EmptyTableState;
