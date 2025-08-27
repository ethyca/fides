import {
  AntForm as Form,
  AntFormItemProps as FormItemProps,
  AntSelect as Select,
} from "fidesui";
import { ComponentProps, useState } from "react";

export type FormikSelectProps = ComponentProps<typeof Select> &
  Pick<
    FormItemProps,
    "required" | "name" | "label" | "tooltip" | "help" | "extra"
  > & {
    error?: string;
    touched?: boolean;
  };

/*
 * @description: Transitory component that migrates away from chakra while retaining formik
 */
export const FormikSelect = ({
  error,
  touched,
  required,
  tooltip,
  label,
  extra,
  name,
  id,
  ...props
}: FormikSelectProps) => {
  const [searchValue, setSearchValue] = useState("");

  // Tags mode requires a custom option, everything else should just pass along the props or undefined
  const optionRender =
    props.mode === "tags"
      ? (option: any, info: any) => {
          if (!option) {
            return undefined;
          }
          if (
            option.value === searchValue &&
            !props.value?.includes(searchValue)
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

  return (
    <Form.Item
      validateStatus={touched && !!error ? "error" : undefined}
      help={touched && error}
      hasFeedback={touched && !!error}
      required={required}
      tooltip={tooltip}
      label={label}
      extra={extra}
      htmlFor={id ?? name}
    >
      <Select
        id={id ?? name}
        data-testid={`controlled-select-${name}`}
        {...props}
        optionRender={optionRender}
        onSearch={props.mode === "tags" ? handleSearch : undefined}
      />
    </Form.Item>
  );
};
