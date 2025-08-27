import {
  AntForm as Form,
  AntFormItemProps as FormItemProps,
  LocationSelect,
  LocationSelectProps,
} from "fidesui";

export type FormikLocationSelectProps = LocationSelectProps &
  Pick<
    FormItemProps,
    "required" | "name" | "label" | "tooltip" | "help" | "extra"
  > & {
    touched?: boolean;
    error?: string;
  };

export const FormikLocationSelect = ({
  error,
  touched,
  required,
  tooltip,
  label,
  extra,
  name,
  id,
  ...props
}: FormikLocationSelectProps) => {
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
      <LocationSelect
        id={id ?? name}
        data-testid={`controlled-select-${name}`}
        {...props}
      />
    </Form.Item>
  );
};
