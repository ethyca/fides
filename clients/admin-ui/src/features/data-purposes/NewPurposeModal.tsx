import { Form, Input, Select, useMessage } from "fidesui";
import { useMemo } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import ConfirmCloseModal from "~/features/common/modals/ConfirmCloseModal";
import { useGetAllDataUsesQuery } from "~/features/data-use/data-use.slice";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import { RTKErrorResult } from "~/types/errors/api";

import { useCreateDataPurposeMutation } from "./data-purpose.slice";

interface NewPurposeModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: (fidesKey: string) => void;
}

const NewPurposeModal = ({
  open,
  onClose,
  onCreated,
}: NewPurposeModalProps) => {
  const [form] = Form.useForm();
  const message = useMessage();
  const { data: dataUses } = useGetAllDataUsesQuery();
  const [createDataPurpose, { isLoading }] = useCreateDataPurposeMutation();

  const dataUseOptions = useMemo(
    () =>
      (dataUses ?? []).map((dataUse) => ({
        value: dataUse.fides_key,
        label: dataUse.fides_key,
      })),
    [dataUses],
  );

  const handleFinish = async (values: {
    name: string;
    data_use: string;
    description?: string;
  }) => {
    try {
      const created = await createDataPurpose({
        fides_key: formatKey(values.name),
        name: values.name,
        data_use: values.data_use,
        description: values.description || null,
      }).unwrap();
      form.resetFields();
      onCreated(created.fides_key);
    } catch (error) {
      message.error(getErrorMessage(error as RTKErrorResult["error"]));
    }
  };

  const handleClose = () => {
    form.resetFields();
    onClose();
  };

  return (
    <ConfirmCloseModal
      title="New purpose"
      open={open}
      onClose={handleClose}
      getIsDirty={() => form.isFieldsTouched()}
      onOk={() => form.submit()}
      okText="Create"
      confirmLoading={isLoading}
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
            aria-label="Data use"
            options={dataUseOptions}
            placeholder="Select data use"
            showSearch
          />
        </Form.Item>
        <Form.Item label="Description" name="description">
          <Input.TextArea rows={3} placeholder="Describe this purpose" />
        </Form.Item>
      </Form>
    </ConfirmCloseModal>
  );
};

export default NewPurposeModal;
