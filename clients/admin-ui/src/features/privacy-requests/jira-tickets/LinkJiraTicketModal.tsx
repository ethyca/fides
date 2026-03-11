import {
  Button,
  ChakraModal as Modal,
  ChakraModalBody as ModalBody,
  ChakraModalContent as ModalContent,
  ChakraModalFooter as ModalFooter,
  ChakraModalHeader as ModalHeader,
  ChakraModalOverlay as ModalOverlay,
  Input,
  Space,
  Typography,
  useMessage,
} from "fidesui";
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
    <Modal isOpen={isOpen} onClose={handleCancel} isCentered>
      <ModalOverlay />
      <ModalContent maxWidth="456px" data-testid="link-jira-ticket-modal">
        <ModalHeader>
          <Typography.Title level={4}>Link Jira ticket</Typography.Title>
        </ModalHeader>
        <ModalBody className="flex flex-col gap-4">
          <Typography.Text>
            Enter the Jira ticket key to link to this privacy request (e.g.
            PRIV-123).
          </Typography.Text>
          <Input
            placeholder="PRIV-123"
            value={ticketKey}
            onChange={(e) => setTicketKey(e.target.value)}
            onPressEnter={handleSubmit}
            data-testid="link-jira-ticket-input"
          />
        </ModalBody>
        <ModalFooter>
          <Space>
            <Button
              onClick={handleCancel}
              disabled={isLoading}
              data-testid="link-jira-ticket-cancel"
            >
              Cancel
            </Button>
            <Button
              type="primary"
              onClick={handleSubmit}
              loading={isLoading}
              disabled={!ticketKey.trim()}
              data-testid="link-jira-ticket-confirm"
            >
              Link ticket
            </Button>
          </Space>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default LinkJiraTicketModal;
