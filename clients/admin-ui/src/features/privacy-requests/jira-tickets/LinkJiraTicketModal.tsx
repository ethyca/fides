import { Button, Flex, Modal, useMessage } from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { RTKErrorResult } from "~/types/errors/api";

import { useLinkJiraTicketMutation } from "./privacy-request-jira-tickets.slice";

interface LinkJiraTicketModalProps {
  privacyRequestId: string;
  isOpen: boolean;
  onClose: () => void;
}

const LinkJiraTicketModal = ({
  privacyRequestId,
  isOpen,
  onClose,
}: LinkJiraTicketModalProps) => {
  const [ticketKey, setTicketKey] = useState("");
  const [linkJiraTicket, { isLoading }] = useLinkJiraTicketMutation();
  const message = useMessage();

  const handleSubmit = async () => {
    if (!ticketKey.trim()) {
      return;
    }
    try {
      await linkJiraTicket({
        privacy_request_id: privacyRequestId,
        ticket_key: ticketKey.trim(),
      }).unwrap();
      message.success(`Jira ticket ${ticketKey.trim()} linked successfully.`);
      setTicketKey("");
      onClose();
    } catch (error) {
      message.error(
        getErrorMessage(
          error as RTKErrorResult["error"],
          "Failed to link Jira ticket.",
        ),
      );
    }
  };

  const handleCancel = () => {
    setTicketKey("");
    onClose();
  };

  return (
    <Modal
      open={isOpen}
      onCancel={handleCancel}
      centered
      destroyOnHidden
      title="Link Jira ticket"
      footer={null}
      data-testid="link-jira-ticket-modal"
    >
      <div className="mb-2 text-sm text-gray-500">
        Enter the Jira ticket key to link to this privacy request (e.g.
        PRIV-123).
      </div>
      <input
        className="w-full rounded border border-gray-300 p-2 text-sm"
        placeholder="PRIV-123"
        value={ticketKey}
        onChange={(e) => setTicketKey(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
        data-testid="link-jira-ticket-input"
      />
      <Flex justify="flex-end" className="mt-4" gap="small">
        <Button
          disabled={isLoading}
          onClick={handleCancel}
          data-testid="link-jira-ticket-cancel"
        >
          Cancel
        </Button>
        <Button
          type="primary"
          loading={isLoading}
          disabled={!ticketKey.trim()}
          onClick={handleSubmit}
          data-testid="link-jira-ticket-confirm"
        >
          Link ticket
        </Button>
      </Flex>
    </Modal>
  );
};

export default LinkJiraTicketModal;
