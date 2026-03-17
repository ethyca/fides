import { Collapse, Form, Input, Modal, Select } from "fidesui";
import { useEffect } from "react";

import { DatasetField } from "~/types/api";

import FieldMetadataFormItems, {
  buildFieldMeta,
} from "./FieldMetadataFormItems";

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
  const fidesMeta = buildFieldMeta(values);

  if (!description && !dataCategories && !fidesMeta) {
    return undefined;
  }

  return {
    description,
    data_categories: dataCategories,
    fides_meta: fidesMeta,
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
                  children: <FieldMetadataFormItems />,
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
