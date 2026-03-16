import {
  Button,
  ChakraDeleteIcon as DeleteIcon,
  ChakraFlex as Flex,
  ChakraSmallAddIcon as SmallAddIcon,
} from "fidesui";
import { FieldArray, useFormikContext } from "formik";

import { CustomTextInput } from "~/features/common/form/inputs";

import type { PropertyFormValues } from "../PropertyForm";

const PathsFieldArray = () => {
  const { values } = useFormikContext<PropertyFormValues>();
  const paths = values.paths ?? [];

  return (
    <FieldArray
      name="paths"
      render={(arrayHelpers) => (
        <Flex flexDir="column" gap={3}>
          {paths.map((_, index) => (
            // eslint-disable-next-line react/no-array-index-key
            <Flex key={index} flexDir="row" gap={2} alignItems="flex-end">
              <Flex flex={1}>
                <CustomTextInput
                  name={`paths[${index}]`}
                  label={index === 0 ? "Path" : undefined}
                  placeholder="/path"
                  variant="stacked"
                />
              </Flex>
              <Button
                aria-label="Remove path"
                icon={<DeleteIcon />}
                onClick={() => arrayHelpers.remove(index)}
                loading={false}
                className="mb-1"
                data-testid={`remove-path-${index}`}
              />
            </Flex>
          ))}
          <Button
            icon={<SmallAddIcon />}
            onClick={() => arrayHelpers.push("")}
            loading={false}
            data-testid="add-path-button"
          >
            Add path
          </Button>
        </Flex>
      )}
    />
  );
};

export default PathsFieldArray;
