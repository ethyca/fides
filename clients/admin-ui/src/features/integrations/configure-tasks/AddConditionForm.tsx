import { Dayjs } from "dayjs";
import {
  AntButton as Button,
  AntForm as Form,
  AntRadio as Radio,
  AntSelect as Select,
  Flex,
  RadioChangeEvent,
} from "fidesui";
import { useCallback, useEffect, useState } from "react";

import { DatasetReferencePicker } from "~/features/common/dataset";
import { useFlags } from "~/features/common/features/features.slice";
import { ConditionLeaf, Operator } from "~/types/api";

import { ConditionValueSelector } from "./components/ConditionValueSelector";
import { OperatorReferenceGuide } from "./components/OperatorReferenceGuide";
import { PrivacyRequestFieldPicker } from "./components/PrivacyRequestFieldPicker";
import { FieldSource } from "./types";
import {
  getFieldType,
  getInitialFieldSource,
  getValueTooltip,
  OPERATOR_OPTIONS,
  parseConditionValue,
} from "./utils";

interface FormValues {
  fieldAddress: string;
  operator: Operator;
  value?: string | boolean | Dayjs;
}

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
  const { flags } = useFlags();

  // Check if privacy request field conditions feature is enabled
  const privacyRequestFieldConditionsEnabled =
    flags.alphaPrivacyRequestFieldConditions ?? false;

  const [fieldSource, setFieldSource] = useState<FieldSource>(
    getInitialFieldSource(editingCondition),
  );

  // Watch the selected field to determine its type
  const selectedFieldAddress = Form.useWatch("fieldAddress", form);
  const selectedFieldType = selectedFieldAddress
    ? getFieldType(selectedFieldAddress)
    : "string";

  // Set initial values if editing
  const initialValues = editingCondition
    ? {
        fieldSource: getInitialFieldSource(editingCondition),
        fieldAddress: editingCondition.field_address,
        operator: editingCondition.operator,
        value: editingCondition.value?.toString() || "",
      }
    : {
        fieldSource: FieldSource.DATASET,
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
    setFieldSource(FieldSource.DATASET);
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
      {privacyRequestFieldConditionsEnabled && (
        <Form.Item
          name="fieldSource"
          label="Field source"
          rules={[{ required: true, message: "Field source is required" }]}
        >
          <Radio.Group onChange={handleFieldSourceChange}>
            <Radio
              value={FieldSource.PRIVACY_REQUEST}
              data-testid="field-source-privacy-request"
            >
              Privacy request field
            </Radio>
            <Radio
              value={FieldSource.DATASET}
              data-testid="field-source-dataset"
            >
              Dataset field
            </Radio>
          </Radio.Group>
        </Form.Item>
      )}

      <Form.Item
        name="fieldAddress"
        label="Field"
        rules={[{ required: true, message: "Field is required" }]}
        tooltip={
          !privacyRequestFieldConditionsEnabled ||
          fieldSource === FieldSource.DATASET
            ? "Select a field from your datasets to use in the condition"
            : "Select a privacy request field to use in the condition"
        }
        validateTrigger={["onBlur", "onSubmit"]}
      >
        {privacyRequestFieldConditionsEnabled &&
        fieldSource === FieldSource.PRIVACY_REQUEST ? (
          <PrivacyRequestFieldPicker connectionKey={connectionKey} />
        ) : (
          <DatasetReferencePicker />
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
        tooltip={getValueTooltip(selectedFieldType, isValueDisabled)}
      >
        <ConditionValueSelector
          fieldType={selectedFieldType}
          disabled={isValueDisabled}
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
