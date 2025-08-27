import {
  AntDatePicker as DatePicker,
  AntDatePickerProps as DatePickerProps,
  AntForm as Form,
  AntFormItemProps as FormItemProps,
} from "fidesui";

/*
 * @description: Transitory component that migrates away from chakra while retaining formik
 */
export const FormikDateTimeInput = ({
  error,
  touched,
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
      validateStatus={touched && !!error ? "error" : undefined}
      help={touched && error}
      hasFeedback={touched && !!error}
      required={required}
      tooltip={tooltip}
      label={label}
      extra={extra}
      htmlFor={id ?? name}
    >
      <DatePicker
        id={id ?? name}
        name={name}
        data-testid={`input-${name}`}
        style={{
          width: "100%",
          ...props.style,
        }}
        {...props}
      />
    </Form.Item>
  );
};
