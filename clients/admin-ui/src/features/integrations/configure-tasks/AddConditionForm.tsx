import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntSelect as Select,
  Flex,
} from "fidesui";
import { useCallback, useEffect } from "react";

import { DatasetReferencePicker } from "~/features/common/dataset";
import { ConditionLeaf, Operator } from "~/types/api";

interface FormValues {
  fieldAddress: string;
  operator: Operator;
  value?: string;
}

// Utility function to parse condition value
const parseConditionValue = (
  operator: Operator,
  rawValue?: string,
): string | number | boolean | null => {
  if (operator === Operator.EXISTS || operator === Operator.NOT_EXISTS) {
    return null;
  }

  if (!rawValue?.trim()) {
    return null;
  }

  // Try boolean first
  if (rawValue.toLowerCase() === "true") {
    return true;
  }
  if (rawValue.toLowerCase() === "false") {
    return false;
  }

  // Try number
  const numValue = Number(rawValue);
  if (!Number.isNaN(numValue)) {
    return numValue;
  }

  // Default to string
  return rawValue;
};

interface AddConditionFormProps {
  onAdd: (condition: ConditionLeaf) => void;
  onCancel: () => void;
  editingCondition?: ConditionLeaf | null;
  isSubmitting?: boolean;
}

const AddConditionForm = ({
  onAdd,
  onCancel,
  editingCondition,
  isSubmitting = false,
}: AddConditionFormProps) => {
  const [form] = Form.useForm();
  const isEditing = !!editingCondition;

  // Operator options for the select dropdown
  const operatorOptions = [
    { label: "Equals", value: Operator.EQ },
    { label: "Not equals", value: Operator.NEQ },
    { label: "Greater than", value: Operator.GT },
    { label: "Greater than or equal", value: Operator.GTE },
    { label: "Less than", value: Operator.LT },
    { label: "Less than or equal", value: Operator.LTE },
    { label: "Exists", value: Operator.EXISTS },
    { label: "Does not exist", value: Operator.NOT_EXISTS },
    { label: "List contains", value: Operator.LIST_CONTAINS },
    { label: "Not in list", value: Operator.NOT_IN_LIST },
  ];

  // Set initial values if editing
  const initialValues = editingCondition
    ? {
        fieldAddress: editingCondition.field_address,
        operator: editingCondition.operator,
        value: editingCondition.value?.toString() || "",
      }
    : {};

  const handleSubmit = useCallback(
    (values: FormValues) => {
      const condition: ConditionLeaf = {
        field_address: values.fieldAddress.trim(),
        operator: values.operator,
        value: parseConditionValue(values.operator, values.value),
      };

      onAdd(condition);
      // Don't reset form here - let the modal handle it on successful save
    },
    [onAdd],
  );

  const handleCancel = useCallback(() => {
    form.resetFields();
    onCancel();
  }, [form, onCancel]);

  // Check if value field should be disabled
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
        label="Dataset Field"
        rules={[{ required: true, message: "Dataset field is required" }]}
        tooltip="Select a field from your datasets to use in the condition"
      >
        <DatasetReferencePicker />
      </Form.Item>

      <Form.Item
        name="operator"
        label="Operator"
        rules={[{ required: true, message: "Operator is required" }]}
      >
        <Select placeholder="Select operator" options={operatorOptions} />
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
            ? "Value is not required for exists/not exists operators"
            : "Enter the value to compare against. Can be text, number, or true/false"
        }
      >
        <Input
          placeholder={
            isValueDisabled
              ? "Not required"
              : "Enter value (text, number, or true/false)"
          }
          disabled={isValueDisabled}
        />
      </Form.Item>

      <Form.Item>
        <Flex gap={2} justify="flex-end">
          <Button onClick={handleCancel} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="primary" htmlType="submit" loading={isSubmitting}>
            {isEditing ? "Update" : "Add"}
          </Button>
        </Flex>
      </Form.Item>
    </Form>
  );
};

export default AddConditionForm;
