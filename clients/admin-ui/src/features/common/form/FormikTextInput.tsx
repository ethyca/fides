import {
  AntForm as Form,
  AntFormItemProps as FormItemProps,
  AntInput as Input,
  AntInputProps as InputProps,
} from "fidesui";
import React from "react";

export const FormikTextInput = ({
  error,
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
  }) => {
  return (
    <Form.Item
      validateStatus={error ? "error" : undefined}
      help={error}
      required={required}
      tooltip={tooltip}
      label={label}
      hasFeedback={!!error}
      extra={extra}
      htmlFor={id ?? name}
    >
      <Input id={id || name} data-testid={`input-${name}`} {...props} />
    </Form.Item>
  );
};
