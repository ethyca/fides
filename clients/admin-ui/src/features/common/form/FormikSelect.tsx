import {
  AntForm as Form,
  AntSelect as Select,
  AntSelectProps as SelectProps,
  FormLabelProps,
} from "fidesui";
import { useField } from "formik";
import { useState } from "react";

export interface FormikSelectProps extends SelectProps {
  name: string;
  label?: string;
  labelProps?: FormLabelProps;
  tooltip?: string | null;
  isRequired?: boolean;
  layout?: "inline" | "stacked";
  helperText?: string | null;
}

/*
 * @description: Transitory component that migrates away from chakra while retaining formik
 */
export const FormikSelect = ({
  name,
  label,
  labelProps,
  tooltip,
  isRequired,
  layout = "inline",
  helperText,
  ...props
}: FormikSelectProps) => {
  const [field, meta, { setValue }] = useField(name);
  const isInvalid = !!(meta.touched && meta.error);
  const [searchValue, setSearchValue] = useState("");

  if (!field.value && (props.mode === "tags" || props.mode === "multiple")) {
    field.value = [];
  }
  if (props.mode === "tags" && typeof field.value === "string") {
    field.value = [field.value];
  }

  // Tags mode requires a custom option, everything else should just pass along the props or undefined
  const optionRender =
    props.mode === "tags"
      ? (option: any, info: any) => {
          if (!option) {
            return undefined;
          }
          if (
            option.value === searchValue &&
            !field.value.includes(searchValue)
          ) {
            return `Create "${searchValue}"`;
          }
          if (props.optionRender) {
            return props.optionRender(option, info);
          }
          return option.label;
        }
      : props.optionRender || undefined;

  // this just supports the custom tag option, otherwise it's completely unnecessary
  const handleSearch = (value: string) => {
    setSearchValue(value);
    if (props.onSearch) {
      props.onSearch(value);
    }
  };

  // Pass the value to the formik field
  const handleChange = (newValue: any, option: any) => {
    setValue(newValue);
    if (props.onChange) {
      props.onChange(newValue, option);
    }
  };

  return (
    <Form.Item
      status={isInvalid ? "error" : undefined}
      help={isInvalid && meta.error}
      required={isRequired}
      tooltip={tooltip}
      label={label}
      extra={helperText}
      htmlFor={props.id ?? name}
      layout={
        layout === "inline" ? "horizontal" : "vertical"
      } /* Legacy layout prop names */
    >
      <Select
        {...field}
        id={props.id ?? name}
        data-testid={`controlled-select-${field.name}`}
        {...props}
        optionRender={optionRender}
        onSearch={props.mode === "tags" ? handleSearch : undefined}
        onChange={handleChange}
        value={field.value || undefined} // solves weird bug where placeholder won't appear if value is an empty string ""
        status={isInvalid ? "error" : undefined}
      />
    </Form.Item>
  );
};
