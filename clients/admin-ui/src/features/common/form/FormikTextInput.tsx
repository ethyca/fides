import {
  AntForm as Form,
  AntFormItemProps as FormItemProps,
  AntInput as Input,
  AntInputProps as InputProps,
} from "fidesui";
import React from "react";

export const FormikTextInput = ({
  error,
  touched,
  required,
  tooltip,
  label,
  extra,
  name,
  id,
  ...props
}: InputProps &
  Pick<
    FormItemProps,
    "required" | "name" | "label" | "tooltip" | "help" | "extra"
  > & {
    error?: string;
    touched?: boolean;
  }) => {
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
      <Input
        id={id || name}
        name={name}
        data-testid={`input-${name}`}
        allowClear
        {...props}
      />
    </Form.Item>
  );
};
