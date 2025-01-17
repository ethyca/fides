import type { AntRadioGroupProps as RadioGroupProps } from "fidesui";
import {
  AntFlex as Flex,
  AntRadio as Radio,
  FormControl,
  Grid,
  RadioChangeEvent,
  Text,
} from "fidesui";
import { useField } from "formik";

import type { StringField } from "~/features/common/form/inputs";
import { ErrorMessage, Label, Option } from "~/features/common/form/inputs";
import QuestionTooltip from "~/features/common/QuestionTooltip";

interface ControlledRadioGroupProps extends RadioGroupProps {
  label?: string;
  options: Option[];
  layout?: "inline" | "stacked";
  defaultFirstSelected?: boolean;
}

const ControlledRadioGroup = ({
  label,
  options,
  layout,
  defaultFirstSelected = true,
  ...props
}: ControlledRadioGroupProps & StringField) => {
  const [initialField, meta] = useField(props);
  const field = { ...initialField, value: initialField.value ?? "" };
  const isInvalid = !!(meta.touched && meta.error);
  const defaultSelected = defaultFirstSelected ? options[0] : undefined;
  const selected =
    options.find((o) => o.value === field.value) ?? defaultSelected;

  const handleChange = (e: RadioChangeEvent) => {
    field.onChange(props.name)(e.target.value);
  };

  if (layout === "stacked") {
    return (
      <FormControl isInvalid={isInvalid}>
        <Flex className="w-fit">
          {label ? (
            <Label htmlFor={props.id || props.name}>{label}</Label>
          ) : null}
          <Radio.Group
            onChange={handleChange}
            value={selected?.value}
            data-testid={`input-${field.name}`}
          >
            <Flex className="flex-col gap-3">
              {options.map(
                ({ value, label: optionLabel, tooltip: optionTooltip }) => (
                  <Radio
                    key={value}
                    value={value}
                    data-testid={`option-${value}`}
                  >
                    <Flex className="items-center gap-2">
                      <Text fontSize="sm" fontWeight="medium">
                        {optionLabel}
                      </Text>
                      {optionTooltip ? (
                        <QuestionTooltip label={optionTooltip} />
                      ) : null}
                    </Flex>
                  </Radio>
                ),
              )}
            </Flex>
          </Radio.Group>
        </Flex>
        <ErrorMessage
          isInvalid={isInvalid}
          message={meta.error}
          fieldName={field.name}
        />
      </FormControl>
    );
  }

  return (
    <FormControl isInvalid={isInvalid}>
      <Grid templateColumns="1fr 3fr">
        <Label htmlFor={props.id || props.name}>{label}</Label>
        <Radio.Group
          onChange={handleChange}
          value={selected?.value}
          data-testid={`input-${field.name}`}
        >
          <Flex>
            {options.map((o) => (
              <Radio
                key={o.value}
                value={o.value}
                data-testid={`option-${o.value}`}
              >
                {o.label}
              </Radio>
            ))}
          </Flex>
        </Radio.Group>
      </Grid>
      <ErrorMessage
        isInvalid={isInvalid}
        message={meta.error}
        fieldName={field.name}
      />
    </FormControl>
  );
};

export default ControlledRadioGroup;
