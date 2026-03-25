import { Button, Flex, Modal, Typography, useMessage } from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { RTKErrorResult } from "~/types/errors/api";

import { useForceCloseJiraTicketsMutation } from "./privacy-request-jira-tickets.slice";

interface ForceCloseModalProps {
  privacyRequestId: string;
  isOpen: boolean;
  onClose: () => void;
}

const ForceCloseModal = ({
  privacyRequestId,
  isOpen,
  onClose,
}: ForceCloseModalProps) => {
  const [reason, setReason] = useState("");
  const [forceCloseJiraTickets, { isLoading }] =
    useForceCloseJiraTicketsMutation();
  const message = useMessage();

  const handleSubmit = async () => {
    try {
      await forceCloseJiraTickets({
        privacy_request_id: privacyRequestId,
        reason: reason.trim() || null,
      }).unwrap();
      message.success("Privacy request Jira gates force-closed successfully.");
      setReason("");
      onClose();
    } catch (error) {
      message.error(
        getErrorMessage(
          error as RTKErrorResult["error"],
          "Failed to force close Jira gates.",
        ),
      );
    }
  };

  const handleCancel = () => {
    setReason("");
    onClose();
  };

  return (
    <Modal
      open={isOpen}
      onCancel={handleCancel}
      centered
      destroyOnHidden
      title="Force close"
      footer={null}
      data-testid="force-close-modal"
    >
      <div className="mb-2 text-sm text-gray-500">
        Force closing will complete all pending Jira gates for this request,
        unblocking the DSR runner. This cannot be undone.
      </div>
      <Typography.Text className="mb-1 block text-sm">
        Reason (optional)
      </Typography.Text>
      <textarea
        className="w-full rounded border border-gray-300 p-2 text-sm"
        rows={3}
        placeholder="Enter a reason for force closing..."
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        data-testid="force-close-reason-input"
      />
      <Flex justify="flex-end" className="mt-4" gap="small">
        <Button disabled={isLoading} onClick={handleCancel}>
          Cancel
        </Button>
        <Button
          danger
          type="primary"
          loading={isLoading}
          onClick={handleSubmit}
          data-testid="force-close-confirm"
        >
          Force close
        </Button>
      </Flex>
    </Modal>
  );
};

export default ForceCloseModal;
