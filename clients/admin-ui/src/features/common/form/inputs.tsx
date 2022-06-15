import {
  FormControl,
  FormErrorMessage,
  FormLabel,
  Input,
  SimpleGrid,
} from "@fidesui/react";
import { Select } from "chakra-react-select";
import { FieldHookConfig, useField } from "formik";

interface InputProps {
  label: string;
}

export const CustomTextInput = ({
  label,
  ...props
}: InputProps & FieldHookConfig<string>) => {
  const [field, meta] = useField(props);
  const { type, placeholder } = props;
  const isInvalid = !!(meta.touched && meta.error);
  return (
    <FormControl isInvalid={isInvalid}>
      <SimpleGrid columns={[1, 2]}>
        <FormLabel htmlFor={props.id || props.name} size="sm">
          {label}
        </FormLabel>
        <Input {...field} type={type} placeholder={placeholder} size="sm" />
      </SimpleGrid>
      {isInvalid ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
    </FormControl>
  );
};

interface Option {
  value: string;
  label: string;
}
interface SelectProps {
  label: string;
  options: Option[];
  isSearchable?: boolean;
}
export const CustomSelect = ({
  label,
  options,
  isSearchable,
  ...props
}: SelectProps & FieldHookConfig<string>) => {
  const [field, meta] = useField(props);

  const isInvalid = !!(meta.touched && meta.error);
  return (
    <FormControl isInvalid={isInvalid}>
      <SimpleGrid columns={[1, 2]}>
        <FormLabel htmlFor={props.id || props.name} size="sm">
          {label}
        </FormLabel>
        <Select
          options={options}
          onBlur={(option) => {
            if (option) {
              field.onBlur(props.name);
            }
          }}
          onChange={(option) => {
            if (option) {
              field.onChange(props.name)(option.value);
            }
          }}
          name={props.name}
          value={options.find((o) => o.value === field.value)}
          size="sm"
          chakraStyles={{
            dropdownIndicator: (provided) => ({
              ...provided,
              bg: "transparent",
              px: 2,
              cursor: "inherit",
            }),
            indicatorSeparator: (provided) => ({
              ...provided,
              display: "none",
            }),
          }}
          isSearchable={isSearchable ?? false}
        />
      </SimpleGrid>
      {isInvalid ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
    </FormControl>
  );
};
