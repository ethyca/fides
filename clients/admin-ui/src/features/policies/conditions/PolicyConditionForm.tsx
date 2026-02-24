import { Button, Flex, Form, Select } from "fidesui";
import { useCallback, useEffect } from "react";

import { ConditionValueSelector } from "~/features/integrations/configure-tasks/components/ConditionValueSelector";
import {
  getFieldType,
  parseConditionValue,
  parseStoredValueForForm,
} from "~/features/integrations/configure-tasks/utils";
import type { ConditionLeaf, Operator } from "~/types/api";
import { Operator as Op } from "~/types/api";

const FIELD_OPTIONS = [
  { label: "State/Province", value: "privacy_request.location" },
  { label: "Country/Territory", value: "privacy_request.location_country" },
  { label: "Groups", value: "privacy_request.location_groups" },
  { label: "Regulation", value: "privacy_request.location_regulations" },
];

const POLICY_OPERATOR_OPTIONS = [
  { label: "Equals", value: Op.EQ },
  { label: "List contains", value: Op.LIST_CONTAINS },
];

interface FormValues {
  fieldAddress: string;
  operator: Operator;
  value?: string;
}

interface PolicyConditionFormProps {
  onSubmit: (condition: ConditionLeaf) => void;
  onCancel: () => void;
  editingCondition?: ConditionLeaf | null;
  isSubmitting?: boolean;
}

export const PolicyConditionForm = ({
  onSubmit,
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

  const isOperatorFixed =
    selectedFieldType === "location_groups" ||
    selectedFieldType === "location_regulations";

  useEffect(() => {
    if (isOperatorFixed) {
      form.setFieldValue("operator", Op.LIST_CONTAINS);
    }
  }, [isOperatorFixed, form]);

  useEffect(() => {
    if (form.isFieldTouched("fieldAddress")) {
      form.setFieldValue("value", undefined);
    }
  }, [selectedFieldAddress, form]);

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

  const handleSubmit = useCallback(
    (values: FormValues) => {
      const condition: ConditionLeaf = {
        field_address: values.fieldAddress,
        operator: values.operator,
        value: parseConditionValue(values.operator, values.value),
      };
      onSubmit(condition);
    },
    [onSubmit],
  );

  const handleCancel = useCallback(() => {
    form.resetFields();
    onCancel();
  }, [form, onCancel]);

  return (
    <Form
      form={form}
      onFinish={handleSubmit}
      layout="vertical"
      initialValues={initialValues}
    >
      <Form.Item
        name="fieldAddress"
        label="Location field"
        rules={[{ required: true, message: "Field is required" }]}
      >
        <Select
          placeholder="Select a location field"
          aria-label="Select a location field"
          options={FIELD_OPTIONS}
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
          options={POLICY_OPERATOR_OPTIONS}
          data-testid="operator-select"
          disabled={isOperatorFixed}
        />
      </Form.Item>

      <Form.Item
        name="value"
        label="Value"
        rules={[{ required: true, message: "Value is required" }]}
      >
        <ConditionValueSelector
          fieldType={selectedFieldType}
          fieldAddress={selectedFieldAddress}
        />
      </Form.Item>

      <Form.Item>
        <Flex gap={8} justify="flex-end">
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
            data-testid="save-condition-btn"
          >
            {isEditing ? "Update" : "Add"}
          </Button>
        </Flex>
      </Form.Item>
    </Form>
  );
};
