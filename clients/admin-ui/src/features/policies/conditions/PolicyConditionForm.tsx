import { Dayjs } from "dayjs";
import { Button, ChakraFlex as Flex, Form, Input, Select } from "fidesui";
import { useCallback, useEffect } from "react";

import {
  getFieldType,
  OPERATOR_OPTIONS,
  parseConditionValue,
  parseStoredValueForForm,
} from "~/features/integrations/configure-tasks/utils";
import { ConditionLeaf, Operator } from "~/types/api";

interface FormValues {
  fieldAddress: string;
  operator: Operator;
  value?: string | boolean | Dayjs;
}

interface PolicyConditionFormProps {
  onAdd: (condition: ConditionLeaf) => void;
  onCancel: () => void;
  editingCondition?: ConditionLeaf | null;
  isSubmitting?: boolean;
}

// Common privacy request fields for policy conditions
const privacyRequestFields = [
  { value: "privacy_request.status", label: "Status" },
  { value: "privacy_request.policy.key", label: "Policy Key" },
  { value: "privacy_request.action_type", label: "Action Type" },
  { value: "privacy_request.location", label: "Location" },
  { value: "privacy_request.location_country", label: "Location Country" },
  { value: "privacy_request.location_groups", label: "Location Groups" },
  {
    value: "privacy_request.location_regulations",
    label: "Location Regulations",
  },
  { value: "privacy_request.created_at", label: "Created At" },
  { value: "privacy_request.identity.email", label: "Identity Email" },
  { value: "privacy_request.identity.phone_number", label: "Identity Phone" },
];

const PolicyConditionForm = ({
  onAdd,
  onCancel,
  editingCondition,
  isSubmitting = false,
}: PolicyConditionFormProps) => {
  const [form] = Form.useForm();
  const isEditing = !!editingCondition;

  const selectedFieldAddress = Form.useWatch("fieldAddress", form);
  const selectedFieldType = selectedFieldAddress
    ? getFieldType(selectedFieldAddress)
    : "string";

  // Set initial values if editing
  const initialValues = editingCondition
    ? {
        fieldAddress: editingCondition.field_address,
        operator: editingCondition.operator,
        value: parseStoredValueForForm(
          editingCondition.field_address,
          editingCondition.value,
        ),
      }
    : {};

  // Reset value when field changes
  useEffect(() => {
    if (form.isFieldTouched("fieldAddress")) {
      form.setFieldValue("value", undefined);
    }
  }, [selectedFieldAddress, form]);

  const handleSubmit = useCallback(
    (values: FormValues) => {
      const condition: ConditionLeaf = {
        field_address: values.fieldAddress.trim(),
        operator: values.operator,
        value: parseConditionValue(values.operator, values.value),
      };

      onAdd(condition);
    },
    [onAdd],
  );

  const handleCancel = useCallback(() => {
    form.resetFields();
    onCancel();
  }, [form, onCancel]);

  const selectedOperator = Form.useWatch("operator", form);
  const isValueDisabled =
    selectedOperator === Operator.EXISTS ||
    selectedOperator === Operator.NOT_EXISTS;

  // Clear value field when operator changes to EXISTS or NOT_EXISTS
  useEffect(() => {
    if (isValueDisabled) {
      form.setFieldValue("value", "");
    }
  }, [isValueDisabled, form]);

  return (
    <Form
      form={form}
      onFinish={handleSubmit}
      layout="vertical"
      initialValues={initialValues}
    >
      <Form.Item
        name="fieldAddress"
        label="Field"
        rules={[{ required: true, message: "Field is required" }]}
        tooltip="Select a privacy request field to use in the condition"
      >
        {/* eslint-disable-next-line jsx-a11y/control-has-associated-label */}
        <Select
          placeholder="Select a field"
          options={privacyRequestFields}
          showSearch
          filterOption={(input, option) =>
            (option?.label?.toString() ?? "")
              .toLowerCase()
              .includes(input.toLowerCase())
          }
          data-testid="field-select"
        />
      </Form.Item>

      <Form.Item
        name="operator"
        label="Operator"
        rules={[{ required: true, message: "Operator is required" }]}
      >
        <Select
          placeholder="Select operator"
          aria-label="Select operator"
          options={OPERATOR_OPTIONS}
          data-testid="operator-select"
        />
      </Form.Item>

      <Form.Item
        name="value"
        label="Value"
        rules={[
          {
            required: !isValueDisabled,
            message: "Value is required for this operator",
          },
        ]}
        tooltip={
          isValueDisabled
            ? "No value needed for this operator"
            : `Enter a ${selectedFieldType} value`
        }
      >
        <Input
          placeholder="Enter value"
          disabled={isValueDisabled}
          data-testid="value-input"
        />
      </Form.Item>

      <Form.Item>
        <Flex gap={2} justify="flex-end">
          <Button
            onClick={handleCancel}
            disabled={isSubmitting}
            data-testid="cancel-btn"
          >
            Cancel
          </Button>
          <Button
            type="primary"
            htmlType="submit"
            loading={isSubmitting}
            data-testid="save-btn"
          >
            {isEditing ? "Update" : "Add"}
          </Button>
        </Flex>
      </Form.Item>
    </Form>
  );
};

export default PolicyConditionForm;
