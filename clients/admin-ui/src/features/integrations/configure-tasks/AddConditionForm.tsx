import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntRadio as Radio,
  AntSelect as Select,
  Flex,
  RadioChangeEvent,
} from "fidesui";
import { useCallback, useEffect, useState } from "react";

import { DatasetReferencePicker } from "~/features/common/dataset";
import { ConditionLeaf, Operator } from "~/types/api";

import { OperatorReferenceGuide } from "./components/OperatorReferenceGuide";
import { PrivacyRequestFieldPicker } from "./components/PrivacyRequestFieldPicker";
import { FieldSource } from "./types";

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
  connectionKey: string;
}

const AddConditionForm = ({
  onAdd,
  onCancel,
  editingCondition,
  isSubmitting = false,
  connectionKey,
}: AddConditionFormProps) => {
  const [form] = Form.useForm();
  const isEditing = !!editingCondition;

  // Determine initial field source based on editing condition
  const getInitialFieldSource = (): FieldSource => {
    if (editingCondition?.field_address) {
      // Privacy request fields start with "privacy_request."
      // Dataset fields contain ":"
      return editingCondition.field_address.startsWith("privacy_request.")
        ? "privacy_request"
        : "dataset";
    }
    return "dataset";
  };

  const [fieldSource, setFieldSource] = useState<FieldSource>(
    getInitialFieldSource(),
  );

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
    { label: "Starts with", value: Operator.STARTS_WITH },
    { label: "Contains", value: Operator.CONTAINS },
  ];

  // Set initial values if editing
  const initialValues = editingCondition
    ? {
        fieldSource: getInitialFieldSource(),
        fieldAddress: editingCondition.field_address,
        operator: editingCondition.operator,
        value: editingCondition.value?.toString() || "",
      }
    : {
        fieldSource: "dataset" as FieldSource,
      };

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
    setFieldSource("dataset");
    onCancel();
  }, [form, onCancel]);

  // Handle field source change
  const handleFieldSourceChange = useCallback(
    (e: RadioChangeEvent) => {
      const newSource = e.target.value as FieldSource;
      setFieldSource(newSource);
      // Clear field address, operator, and value when switching sources
      form.setFieldsValue({
        fieldAddress: undefined,
        operator: undefined,
        value: "",
      });
    },
    [form],
  );

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
        name="fieldSource"
        label="Field source"
        rules={[{ required: true, message: "Field source is required" }]}
      >
        <Radio.Group onChange={handleFieldSourceChange}>
          <Radio
            value="privacy_request"
            data-testid="field-source-privacy-request"
          >
            Privacy request field
          </Radio>
          <Radio value="dataset" data-testid="field-source-dataset">
            Dataset field
          </Radio>
        </Radio.Group>
      </Form.Item>

      <Form.Item
        name="fieldAddress"
        label="Field"
        rules={[{ required: true, message: "Field is required" }]}
        tooltip={
          fieldSource === "dataset"
            ? "Select a field from your datasets to use in the condition"
            : "Select a privacy request field to use in the condition"
        }
        validateTrigger={["onBlur", "onSubmit"]}
      >
        {fieldSource === "dataset" ? (
          <DatasetReferencePicker />
        ) : (
          <PrivacyRequestFieldPicker connectionKey={connectionKey} />
        )}
      </Form.Item>

      <Form.Item
        name="operator"
        label="Operator"
        tooltip={{
          placement: "right",
          title: <OperatorReferenceGuide />,
          styles: {
            root: {
              maxWidth: "500px",
            },
          },
        }}
        rules={[{ required: true, message: "Operator is required" }]}
      >
        <Select
          placeholder="Select operator"
          aria-label="Select operator"
          options={operatorOptions}
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

export default AddConditionForm;
