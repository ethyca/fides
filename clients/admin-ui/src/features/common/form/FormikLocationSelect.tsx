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
      status={error ? "error" : undefined}
      help={error}
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
