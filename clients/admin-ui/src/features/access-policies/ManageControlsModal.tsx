import {
  Button,
  Flex,
  Form,
  Icons,
  Input,
  Modal,
  Popconfirm,
  Text,
  Tooltip,
  useMessage,
} from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";

import {
  useCreateControlMutation,
  useDeleteControlMutation,
  useGetControlsQuery,
  useUpdateControlMutation,
} from "./access-policies.slice";

interface ManageControlsModalProps {
  open: boolean;
  onClose: () => void;
}

/**
 * Slugify a label into a valid control key: lowercase, replace non-alphanumeric
 * runs with underscores, trim leading/trailing underscores.
 */
const slugify = (value: string): string =>
  value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");

const ManageControlsModal = ({ open, onClose }: ManageControlsModalProps) => {
  const message = useMessage();
  const { data: controls = [], isLoading } = useGetControlsQuery(undefined, {
    skip: !open,
  });

  const [createControl, { isLoading: isCreating }] = useCreateControlMutation();
  const [updateControl, { isLoading: isUpdating }] = useUpdateControlMutation();
  const [deleteControl] = useDeleteControlMutation();

  // Inline editing state
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);

  const [editForm] = Form.useForm<{ label: string }>();
  const [addForm] = Form.useForm<{ key: string; label: string }>();

  const handleStartEdit = (key: string, label: string) => {
    setEditingKey(key);
    setIsAdding(false);
    editForm.setFieldsValue({ label });
  };

  const handleCancelEdit = () => {
    setEditingKey(null);
    editForm.resetFields();
  };

  const handleSaveEdit = async () => {
    if (!editingKey) {
      return;
    }
    try {
      const { label } = await editForm.validateFields();
      await updateControl({ key: editingKey, label }).unwrap();
      message.success("Control updated");
      setEditingKey(null);
      editForm.resetFields();
    } catch (error: unknown) {
      if (error && typeof error === "object" && "error" in error) {
        message.error(
          getErrorMessage(
            (error as { error: { status: number; data: unknown } }).error,
            "Failed to update control",
          ),
        );
      }
    }
  };

  const handleStartAdd = () => {
    setIsAdding(true);
    setEditingKey(null);
    addForm.resetFields();
  };

  const handleCancelAdd = () => {
    setIsAdding(false);
    addForm.resetFields();
  };

  const handleSaveAdd = async () => {
    try {
      const { key, label } = await addForm.validateFields();
      await createControl({ key, label }).unwrap();
      message.success("Control created");
      setIsAdding(false);
      addForm.resetFields();
    } catch (error: unknown) {
      if (error && typeof error === "object" && "error" in error) {
        const errorMsg = getErrorMessage(
          (error as { error: { status: number; data: unknown } }).error,
          "Failed to create control",
        );
        if (errorMsg.toLowerCase().includes("already exists")) {
          addForm.setFields([
            { name: "key", errors: ["This key already exists"] },
          ]);
        } else {
          message.error(errorMsg);
        }
      }
    }
  };

  const handleDelete = async (key: string) => {
    try {
      await deleteControl(key).unwrap();
      message.success("Control deleted");
    } catch (error: unknown) {
      if (error && typeof error === "object" && "error" in error) {
        message.error(
          getErrorMessage(
            (error as { error: { status: number; data: unknown } }).error,
            "Failed to delete control",
          ),
        );
      }
    }
  };

  const handleLabelChangeForKey = () => {
    const label = addForm.getFieldValue("label") as string;
    const currentKey = addForm.getFieldValue("key") as string;
    // Only auto-slug if the user hasn't manually edited the key
    if (!currentKey || currentKey === slugify(label.slice(0, -1) || "")) {
      addForm.setFieldValue("key", slugify(label));
    }
  };

  const handleClose = () => {
    setEditingKey(null);
    setIsAdding(false);
    editForm.resetFields();
    addForm.resetFields();
    onClose();
  };

  return (
    <Modal
      title="Manage controls"
      open={open}
      onCancel={handleClose}
      footer={null}
      destroyOnHidden
      width={560}
    >
      {controls.length === 0 && !isLoading && !isAdding ? (
        <div className="py-8 text-center">
          <Text type="secondary" className="mb-4 block">
            No controls yet. Add one to start organizing your policies.
          </Text>
          <Button type="primary" onClick={handleStartAdd}>
            Add control
          </Button>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {controls.map((control) => (
            <div
              key={control.key}
              className="flex items-center gap-2 rounded-md border border-solid border-gray-200 px-3 py-2"
            >
              {editingKey === control.key ? (
                <Form
                  form={editForm}
                  className="!mb-0 flex flex-1 items-center gap-2"
                  onFinish={handleSaveEdit}
                >
                  <Form.Item
                    name="label"
                    className="!mb-0 flex-1"
                    rules={[{ required: true, message: "Label is required" }]}
                  >
                    <Input
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === "Escape") {
                          handleCancelEdit();
                        }
                      }}
                    />
                  </Form.Item>
                  <Button
                    type="primary"
                    size="small"
                    htmlType="submit"
                    loading={isUpdating}
                  >
                    Save
                  </Button>
                  <Button size="small" onClick={handleCancelEdit}>
                    Cancel
                  </Button>
                </Form>
              ) : (
                <>
                  <Text className="flex-1">{control.label}</Text>
                  <Text type="secondary" className="text-xs">
                    {control.key}
                  </Text>
                  <Tooltip title="Edit">
                    <Button
                      type="text"
                      size="small"
                      aria-label="Edit"
                      icon={<Icons.Edit size={14} />}
                      onClick={() =>
                        handleStartEdit(control.key, control.label)
                      }
                    />
                  </Tooltip>
                  <Popconfirm
                    title="Delete control"
                    description="Are you sure? This cannot be undone."
                    onConfirm={() => handleDelete(control.key)}
                    okText="Delete"
                    okType="danger"
                  >
                    <Tooltip title="Delete">
                      <Button
                        type="text"
                        size="small"
                        danger
                        aria-label="Delete"
                        icon={<Icons.TrashCan size={14} />}
                      />
                    </Tooltip>
                  </Popconfirm>
                </>
              )}
            </div>
          ))}

          {isAdding ? (
            <div className="rounded-md border border-solid border-blue-200 bg-blue-50 p-3">
              <Form
                form={addForm}
                layout="vertical"
                className="!mb-0"
                onFinish={handleSaveAdd}
              >
                <Flex gap={8}>
                  <Form.Item
                    name="label"
                    label="Label"
                    className="!mb-2 flex-1"
                    rules={[{ required: true, message: "Label is required" }]}
                  >
                    <Input
                      placeholder="e.g. EEA & UK GDPR"
                      autoFocus
                      onChange={handleLabelChangeForKey}
                    />
                  </Form.Item>
                  <Form.Item
                    name="key"
                    label="Key"
                    className="!mb-2 flex-1"
                    rules={[
                      { required: true, message: "Key is required" },
                      {
                        pattern: /^[a-z0-9_]+$/,
                        message: "Lowercase letters, numbers, underscores only",
                      },
                    ]}
                  >
                    <Input placeholder="e.g. eea_uk_gdpr" />
                  </Form.Item>
                </Flex>
                <Flex gap={8}>
                  <Button
                    type="primary"
                    size="small"
                    htmlType="submit"
                    loading={isCreating}
                  >
                    Save
                  </Button>
                  <Button size="small" onClick={handleCancelAdd}>
                    Cancel
                  </Button>
                </Flex>
              </Form>
            </div>
          ) : (
            <Button
              type="dashed"
              className="mt-1"
              icon={<Icons.Add size={14} />}
              onClick={handleStartAdd}
            >
              Add control
            </Button>
          )}
        </div>
      )}
    </Modal>
  );
};

export default ManageControlsModal;
