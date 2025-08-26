import {
  AntDatePicker as DatePicker,
  AntDatePickerProps as DatePickerProps,
  AntForm as Form,
  AntFormItemProps as FormItemProps,
} from "fidesui";

export const FormikDateTimeInput = ({
  error,
  required,
  tooltip,
  label,
  extra,
  name,
  id,
  ...props
}: DatePickerProps &
  Pick<
    FormItemProps,
    "required" | "name" | "label" | "tooltip" | "help" | "extra"
  > & {
    touched?: boolean;
    error?: string;
  }) => {
  return (
    <Form.Item
      validateStatus={error ? "error" : undefined}
      help={error}
      required={required}
      tooltip={tooltip}
      label={label}
      extra={extra}
      htmlFor={id ?? name}
    >
      <DatePicker
        name={name}
        id={id ?? name}
        data-testid={`input-${name}`}
        {...props}
      />
    </Form.Item>
  );
};
