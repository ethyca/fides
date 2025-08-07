import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntSelect as Select,
  AntTypography as Typography,
  Box,
  Flex,
} from "fidesui";
import { useCallback } from "react";

import { ConditionLeaf, Operator } from "~/types/api";

interface AddConditionFormProps {
  onAdd: (condition: ConditionLeaf) => void;
  onCancel: () => void;
  editingCondition?: ConditionLeaf;
}

const AddConditionForm = ({
  onAdd,
  onCancel,
  editingCondition,
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
    <Box className="rounded-lg border border-gray-200 bg-gray-50 p-4">
      <div className="mb-3">
        <Typography.Text strong>
          {isEditing ? "Edit condition" : "Add new condition"}
        </Typography.Text>
      </div>
      <Form
        form={form}
        onFinish={handleSubmit}
        layout="vertical"
        initialValues={initialValues}
        size="small"
      >
        <Flex gap={3}>
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
            className="flex-1"
            tooltip="Use dot notation to access nested fields (e.g., user.age, custom_fields.country, identity.email)"
          >
            <Input
              placeholder="e.g., user.age, custom_fields.country, identity.email"
              size="small"
            />
          </Form.Item>

          <Form.Item
            name="operator"
            label="Operator"
            rules={[{ required: true, message: "Operator is required" }]}
            style={{ minWidth: 180 }}
          >
            <Select
              placeholder="Select operator"
              options={operatorOptions}
              size="small"
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
            style={{ minWidth: 150 }}
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
              size="small"
            />
          </Form.Item>

          <Form.Item label=" " className="mb-0">
            <Flex gap={2}>
              <Button type="primary" htmlType="submit" size="small">
                {isEditing ? "Update" : "Add"}
              </Button>
              <Button onClick={handleCancel} size="small">
                Cancel
              </Button>
            </Flex>
          </Form.Item>
        </Flex>
      </Form>
    </Box>
  );
};

export default AddConditionForm;
