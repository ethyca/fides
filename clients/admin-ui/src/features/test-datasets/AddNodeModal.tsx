import {
  Collapse,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  Switch,
} from "fidesui";
import { useEffect } from "react";

import { DatasetField } from "~/types/api";

const DATA_TYPE_OPTIONS = [
  "string",
  "integer",
  "float",
  "boolean",
  "object_id",
  "object",
].map((v) => ({ label: v, value: v }));

const REDACT_OPTIONS = [
  { label: "None", value: "" },
  { label: "name", value: "name" },
];

interface AddNodeModalProps {
  open: boolean;
  title: string;
  existingNames: string[];
  /** "collection" shows only name; "field" shows name + metadata */
  mode?: "collection" | "field";
  onConfirm: (name: string, fieldData?: Partial<DatasetField>) => void;
  onCancel: () => void;
}

const buildFieldData = (
  values: Record<string, unknown>,
): Partial<DatasetField> | undefined => {
  const description = (values.description as string) || undefined;
  const categories = values.data_categories as string[] | undefined;
  const dataCategories =
    categories && categories.length > 0 ? categories : undefined;

  const redactVal = values.redact as string;
  const fieldMeta = {
    data_type: (values.data_type as string) || undefined,
    identity: (values.identity as string) || undefined,
    primary_key: (values.primary_key as boolean) || undefined,
    read_only: (values.read_only as boolean) || undefined,
    return_all_elements: (values.return_all_elements as boolean) || undefined,
    length:
      values.length !== null &&
      values.length !== undefined &&
      values.length !== ""
        ? (values.length as number)
        : undefined,
    custom_request_field: (values.custom_request_field as string) || undefined,
    redact: redactVal === "name" ? ("name" as const) : undefined,
  };
  const hasAnyMeta = Object.values(fieldMeta).some((v) => v !== undefined);

  if (!description && !dataCategories && !hasAnyMeta) {
    return undefined;
  }

  return {
    description,
    data_categories: dataCategories,
    fides_meta: hasAnyMeta ? fieldMeta : undefined,
  };
};

const AddNodeModal = ({
  open,
  title,
  existingNames,
  mode = "collection",
  onConfirm,
  onCancel,
}: AddNodeModalProps) => {
  const [form] = Form.useForm();

  useEffect(() => {
    if (open) {
      form.resetFields();
    }
  }, [open, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      const name = values.name.trim();
      if (mode === "field") {
        onConfirm(name, buildFieldData(values));
      } else {
        onConfirm(name);
      }
    } catch {
      // validation failed
    }
  };

  return (
    <Modal
      title={title}
      open={open}
      onOk={handleOk}
      onCancel={onCancel}
      width={mode === "field" ? 520 : undefined}
    >
      <Form form={form} layout="vertical" size="small">
        <Form.Item
          label="Name"
          name="name"
          rules={[
            { required: true, message: "Name is required" },
            {
              validator: (_, value) => {
                if (value && existingNames.includes(value.trim())) {
                  return Promise.reject(
                    new Error("A node with this name already exists"),
                  );
                }
                return Promise.resolve();
              },
            },
            {
              pattern: /^[a-zA-Z0-9_]+$/,
              message:
                "Name must contain only letters, numbers, and underscores",
            },
          ]}
        >
          <Input placeholder="Enter a unique name" autoFocus />
        </Form.Item>

        {mode === "field" && (
          <>
            <Form.Item label="Description" name="description">
              <Input.TextArea rows={2} placeholder="Add a description..." />
            </Form.Item>

            <Form.Item label="Data Categories" name="data_categories">
              <Select
                mode="tags"
                placeholder="Add data categories..."
                aria-label="Data Categories"
                style={{ width: "100%" }}
              />
            </Form.Item>

            <Collapse
              size="small"
              items={[
                {
                  key: "field-meta",
                  label: "Field Metadata (fides_meta)",
                  children: (
                    <>
                      <Form.Item label="Data Type" name="data_type">
                        <Select
                          allowClear
                          placeholder="Select data type..."
                          aria-label="Data Type"
                          options={DATA_TYPE_OPTIONS}
                        />
                      </Form.Item>
                      <Form.Item label="Identity" name="identity">
                        <Input placeholder="e.g. email, phone_number" />
                      </Form.Item>
                      <Form.Item
                        label="Primary Key"
                        name="primary_key"
                        valuePropName="checked"
                      >
                        <Switch aria-label="Primary Key" />
                      </Form.Item>
                      <Form.Item
                        label="Read Only"
                        name="read_only"
                        valuePropName="checked"
                      >
                        <Switch aria-label="Read Only" />
                      </Form.Item>
                      <Form.Item
                        label="Return All Elements"
                        name="return_all_elements"
                        valuePropName="checked"
                      >
                        <Switch aria-label="Return All Elements" />
                      </Form.Item>
                      <Form.Item label="Length" name="length">
                        <InputNumber
                          min={0}
                          placeholder="Max length"
                          style={{ width: "100%" }}
                        />
                      </Form.Item>
                      <Form.Item
                        label="Custom Request Field"
                        name="custom_request_field"
                      >
                        <Input placeholder="Custom field name" />
                      </Form.Item>
                      <Form.Item label="Redact" name="redact">
                        <Select aria-label="Redact" options={REDACT_OPTIONS} />
                      </Form.Item>
                    </>
                  ),
                },
              ]}
            />
          </>
        )}
      </Form>
    </Modal>
  );
};

export default AddNodeModal;
