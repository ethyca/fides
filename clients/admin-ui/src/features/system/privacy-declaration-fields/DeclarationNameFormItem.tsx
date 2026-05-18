import { Form, Input } from "fidesui";

interface DeclarationNameFormItemProps {
  disabled?: boolean;
  label?: string;
  tooltip?: string;
}

export const DeclarationNameFormItem = ({
  disabled,
  label = "Processing Activity",
  tooltip = "The personal data processing activity or activities associated with this data use.",
}: DeclarationNameFormItemProps) => (
  <Form.Item name="name" label={label} tooltip={tooltip}>
    <Input data-testid="input-name" disabled={disabled} />
  </Form.Item>
);
