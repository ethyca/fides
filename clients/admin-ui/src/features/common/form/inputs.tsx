import {
  FormControl,
  FormErrorMessage,
  FormLabel,
  Input,
  SimpleGrid,
} from "@fidesui/react";
import { Select } from "chakra-react-select";
import { FieldHookConfig, useField, useFormikContext } from "formik";

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
  isClearable?: boolean;
}
export const CustomSelect = ({
  label,
  options,
  isSearchable,
  isClearable,
  ...props
}: SelectProps & FieldHookConfig<string>) => {
  const [field, meta] = useField(props);
  const isInvalid = !!(meta.touched && meta.error);

  const selected = options.find((o) => o.value === field.value);

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
          onChange={(newValue) => {
            if (newValue) {
              field.onChange(props.name)(newValue.value);
            }
          }}
          name={props.name}
          value={selected}
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
          isClearable={isClearable}
        />
      </SimpleGrid>
      {isInvalid ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
    </FormControl>
  );
};

// mostly the same as CustomSelect except can handle multiple values
// the types are easier when this is a separate component as opposed to
// extending CustomSelect
export const CustomMultiSelect = ({
  label,
  options,
  isSearchable,
  isClearable,
  ...props
}: SelectProps & FieldHookConfig<string[]>) => {
  const [field, meta] = useField(props);
  const isInvalid = !!(meta.touched && meta.error);
  const selected = options.filter((o) => field.value.indexOf(o.value) >= 0);
  // note: for Multiselect we have to do setFieldValue instead of field.onChange
  // because field.onChange only accepts strings or events right now, not string[]
  // https://github.com/jaredpalmer/formik/issues/1667
  const { setFieldValue } = useFormikContext();

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
          onChange={(newValue) => {
            setFieldValue(
              field.name,
              newValue.map((v) => v.value)
            );
          }}
          name={props.name}
          value={selected}
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
          isClearable={isClearable}
          isMulti
        />
      </SimpleGrid>
      {isInvalid ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
    </FormControl>
  );
};
