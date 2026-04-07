import {
  Button,
  ChakraBox as Box,
  ChakraFlex as Flex,
  ChakraText as Text,
  Icons,
} from "fidesui";
import { FieldArray, useFormikContext } from "formik";

import type { PropertyFormValues } from "../PropertyForm";
import ActionEntryForm from "./ActionEntryForm";
import { DEFAULT_ACTION } from "./helpers";

const ActionsFieldArray = () => {
  const { values } = useFormikContext<PropertyFormValues>();
  const actions = values.privacy_center_config?.actions ?? [];

  return (
    <FieldArray
      name="privacy_center_config.actions"
      render={(arrayHelpers) => (
        <Flex flexDir="column" gap={4}>
          {actions.map((action, index) => (
            <Box
              // eslint-disable-next-line react/no-array-index-key
              key={index}
              border="1px solid"
              borderColor="gray.200"
              borderRadius="md"
              p={4}
              data-testid={`action-entry-${index}`}
            >
              <Flex justifyContent="space-between" alignItems="center" mb={4}>
                <Text fontSize="sm" fontWeight="semibold" color="gray.700">
                  Action {index + 1}
                  {action.title ? ` — ${action.title}` : ""}
                </Text>
                <Button
                  aria-label="Remove action"
                  icon={<Icons.TrashCan />}
                  onClick={() => arrayHelpers.remove(index)}
                  loading={false}
                  disabled={actions.length === 1}
                  data-testid={`remove-action-${index}`}
                />
              </Flex>
              <ActionEntryForm index={index} />
            </Box>
          ))}
          <Box>
            <Button
              icon={<Icons.Add />}
              onClick={() => arrayHelpers.push({ ...DEFAULT_ACTION })}
              loading={false}
              data-testid="add-action-button"
            >
              Add action
            </Button>
          </Box>
        </Flex>
      )}
    />
  );
};

export default ActionsFieldArray;
