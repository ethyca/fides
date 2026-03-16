import { Form, Input, Modal } from "fidesui";
import { useEffect } from "react";

interface AddNodeModalProps {
  open: boolean;
  title: string;
  existingNames: string[];
  onConfirm: (name: string) => void;
  onCancel: () => void;
}

const AddNodeModal = ({
  open,
  title,
  existingNames,
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
      onConfirm(values.name.trim());
    } catch {
      // validation failed
    }
  };

  return (
    <Modal title={title} open={open} onOk={handleOk} onCancel={onCancel}>
      <Form form={form} layout="vertical">
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
      </Form>
    </Modal>
  );
};

export default AddNodeModal;
