import { AntFlex as Flex, FormControl } from "fidesui";
import { useField } from "formik";

import { ControlledSelectProps } from "~/features/common/form/ControlledSelect";
import { ErrorMessage, Label } from "~/features/common/form/inputs";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import ConsentCategorySelect from "~/features/data-discovery-and-detection/action-center/ConsentCategorySelect";

const WrappedConsentCategorySelect = ({
  name,
  label,
  labelProps,
  tooltip,
}: ControlledSelectProps) => {
  const [field, meta, { setValue, setTouched }] = useField(name);
  const isInvalid = !!(meta.touched && meta.error);

  return (
    <FormControl isInvalid={isInvalid} isRequired>
      <Flex vertical>
        <Flex align="center">
          {label && (
            <Label htmlFor={name} fontSize="xs" mr={1} {...labelProps}>
              {label}
            </Label>
          )}
          {tooltip && <QuestionTooltip label={tooltip} />}
        </Flex>
        <ConsentCategorySelect
          {...field}
          mode="multiple"
          // show checked options in the dropdown instead of removing them once selected
          selectedTaxonomies={[]}
          onChange={(newValue: any) => {
            setValue(newValue);
          }}
          // needed or else the error message won't show up
          onBlur={() => setTouched(true)}
          variant="outlined"
          autoFocus={false}
          status={isInvalid ? "error" : undefined}
          data-testid={`controlled-select-${name}`}
        />
        <ErrorMessage
          isInvalid={isInvalid}
          message={meta.error}
          fieldName={name}
        />
      </Flex>
    </FormControl>
  );
};

export default WrappedConsentCategorySelect;
