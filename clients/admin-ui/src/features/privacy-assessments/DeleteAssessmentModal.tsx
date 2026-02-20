import { Modal, Space, Text } from "fidesui";

interface DeleteAssessmentModalProps {
  open: boolean;
  isDeleting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export const DeleteAssessmentModal = ({
  open,
  isDeleting,
  onConfirm,
  onCancel,
}: DeleteAssessmentModalProps) => (
  <Modal
    title="Delete assessment"
    open={open}
    onCancel={onCancel}
    onOk={onConfirm}
    okText="Delete"
    okButtonProps={{ danger: true, loading: isDeleting }}
  >
    <Space direction="vertical" size="middle" className="w-full">
      <Text>Are you sure you want to delete this assessment?</Text>
      <Text type="secondary">
        This action cannot be undone. All assessment data, including any
        responses and documentation, will be permanently removed.
      </Text>
    </Space>
  </Modal>
);
