import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntSelect as Select,
  Flex,
} from "fidesui";
import { useCallback } from "react";

import { ConditionLeaf, Operator } from "~/types/api";

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
    (values: any) => {
      // Convert value to appropriate type
      let conditionValue: string | number | boolean | null = values.value;

      // For EXISTS and NOT_EXISTS operators, value should be null
      if (
        values.operator === Operator.EXISTS ||
        values.operator === Operator.NOT_EXISTS
      ) {
        conditionValue = null;
      } else if (values.value) {
        // Try to parse as number if it looks like a number
        const numValue = Number(values.value);
        if (!Number.isNaN(numValue) && values.value.trim() !== "") {
          conditionValue = numValue;
        }
        // Try to parse as boolean
        else if (values.value.toLowerCase() === "true") {
          conditionValue = true;
        } else if (values.value.toLowerCase() === "false") {
          conditionValue = false;
        }
      }

      const condition: ConditionLeaf = {
        field_address: values.fieldAddress.trim(),
        operator: values.operator,
        value: conditionValue,
      };

      onAdd(condition);
      form.resetFields();
    },
    [onAdd, form],
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

  return (
    <Form
      form={form}
      onFinish={handleSubmit}
      layout="vertical"
      initialValues={initialValues}
    >
      <Form.Item
        name="fieldAddress"
        label="Field Path"
        rules={[
          { required: true, message: "Field path is required" },
          {
            pattern: /^[a-zA-Z_][a-zA-Z0-9_.]*$/,
            message:
              "Field path must start with a letter or underscore, and contain only letters, numbers, dots, and underscores",
          },
        ]}
        tooltip="Use dot notation to access nested fields (e.g., user.age, custom_fields.country, identity.email)"
      >
        <Input placeholder="e.g., user.age, custom_fields.country, identity.email" />
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
