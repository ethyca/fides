import { Form, Input, Modal, Select } from "fidesui";

export interface ActionFormValues {
  policy_key: string;
  title: string;
  description: string;
  icon_path: string;
  identity_inputs?: Record<string, "required" | "optional">;
}

interface ActionEditModalProps {
  open: boolean;
  initial: ActionFormValues | null;
  onOk: (values: ActionFormValues) => void;
  onCancel: () => void;
}

export const ActionEditModal: React.FC<ActionEditModalProps> = ({
  open,
  initial,
  onOk,
  onCancel,
}) => {
  const [form] = Form.useForm<ActionFormValues>();

  return (
    <Modal
      open={open}
      title={initial ? "Edit action" : "Add action"}
      okText="Save"
      onOk={async () => {
        const values = await form.validateFields();
        onOk(values);
      }}
      onCancel={onCancel}
      destroyOnHidden
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={initial ?? { identity_inputs: { email: "required" } }}
      >
        <Form.Item
          label="Policy key"
          name="policy_key"
          rules={[{ required: true }]}
        >
          <Input placeholder="default_access_policy" />
        </Form.Item>
        <Form.Item label="Title" name="title" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item
          label="Description"
          name="description"
          rules={[{ required: true }]}
        >
          <Input.TextArea autoSize />
        </Form.Item>
        <Form.Item
          label="Icon path"
          name="icon_path"
          rules={[{ required: true }]}
        >
          <Input placeholder="/icon.svg" />
        </Form.Item>
        <Form.Item
          label="Identity inputs"
          name={["identity_inputs", "email"]}
          tooltip="Whether the privacy center asks for email before this action."
        >
          <Select
            options={[
              { label: "Email required", value: "required" },
              { label: "Email optional", value: "optional" },
            ]}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};
