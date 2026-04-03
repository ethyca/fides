import { Alert, Button, Flex, Icons } from "fidesui";
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
        <Flex vertical gap={12}>
          {paths.map((_, index) => (
            // eslint-disable-next-line react/no-array-index-key
            <Flex key={index} vertical gap={8}>
              {paths[index] === "/" && (
                <Alert
                  type="warning"
                  showIcon
                  message={
                    <>
                      <code>FIDES_PRIVACY_CENTER__USE_API_CONFIG</code> must be
                      set to <code>true</code> when serving the Privacy Center
                      at the root path (<code>/</code>). Update this variable to
                      continue.
                    </>
                  }
                />
              )}
              <Flex gap={12} align="flex-end">
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
                  icon={<Icons.TrashCan />}
                  onClick={() => arrayHelpers.remove(index)}
                  loading={false}
                  data-testid={`remove-path-${index}`}
                />
              </Flex>
            </Flex>
          ))}
          <Button
            icon={<Icons.Add />}
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
