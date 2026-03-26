import { Form, Input, Modal, Select } from "fidesui";
import { useMemo } from "react";

import { useGetAllDataUsesQuery } from "~/features/data-use/data-use.slice";

import { usePurposes } from "./usePurposes";

interface NewPurposeModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: (id: string) => void;
}

const slugify = (text: string): string =>
  text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");

const NewPurposeModal = ({ open, onClose, onCreated }: NewPurposeModalProps) => {
  const [form] = Form.useForm();
  const { createPurpose } = usePurposes();
  const { data: dataUses } = useGetAllDataUsesQuery();

  const dataUseOptions = useMemo(
    () =>
      (dataUses ?? []).map((du) => ({
        value: du.fides_key,
        label: du.fides_key,
      })),
    [dataUses],
  );

  const handleFinish = (values: {
    name: string;
    data_use: string;
    description: string;
  }) => {
    const key = slugify(values.name);
    createPurpose({
      name: values.name,
      key,
      data_use: values.data_use,
      description: values.description || "",
      data_categories: [],
      data_subjects: [],
      legal_basis: "",
      legal_basis_is_flexible: false,
      retention_period_days: null,
      special_category_legal_basis: null,
      features: [],
      sub_types: [],
      updated_at: new Date().toISOString(),
    });
    form.resetFields();
    onCreated(key);
  };

  const handleCancel = () => {
    form.resetFields();
    onClose();
  };

  return (
    <Modal
      title="New purpose"
      open={open}
      onCancel={handleCancel}
      onOk={() => form.submit()}
      okText="Create"
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={handleFinish}>
        <Form.Item
          label="Name"
          name="name"
          rules={[{ required: true, message: "Name is required" }]}
        >
          <Input placeholder="e.g. Analytics" />
        </Form.Item>
        <Form.Item
          label="Data use"
          name="data_use"
          rules={[{ required: true, message: "Data use is required" }]}
        >
          <Select
            options={dataUseOptions}
            placeholder="Select data use"
            showSearch
          />
        </Form.Item>
        <Form.Item label="Description" name="description">
          <Input.TextArea rows={3} placeholder="Describe this purpose" />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default NewPurposeModal;
