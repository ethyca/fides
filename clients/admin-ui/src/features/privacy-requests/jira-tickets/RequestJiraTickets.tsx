import {
  Button,
  CUSTOM_TAG_COLOR,
  Flex,
  Icons,
  Spin,
  Tag,
  Title,
  Tooltip,
  Typography,
  useMessage,
} from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";
import { PrivacyRequestStatus, StatusType } from "~/types/api";
import { RTKErrorResult } from "~/types/errors/api";

import ForceCloseModal from "./ForceCloseModal";
import LinkJiraTicketModal from "./LinkJiraTicketModal";
import {
  useGetJiraTicketsQuery,
  useRefreshJiraTicketMutation,
  useRetryJiraTicketMutation,
} from "./privacy-request-jira-tickets.slice";
import { JiraTicketResult } from "./types";

const statusColorMap: Record<string, CUSTOM_TAG_COLOR> = {
  done: CUSTOM_TAG_COLOR.SUCCESS,
  "in progress": CUSTOM_TAG_COLOR.CAUTION,
  "to do": CUSTOM_TAG_COLOR.INFO,
};

const getStatusColor = (status: string): CUSTOM_TAG_COLOR =>
  statusColorMap[status.toLowerCase()] ?? CUSTOM_TAG_COLOR.DEFAULT;

const LINK_ALLOWED_STATUSES = new Set<string>([
  PrivacyRequestStatus.APPROVED,
  PrivacyRequestStatus.IN_PROCESSING,
  PrivacyRequestStatus.PAUSED,
  PrivacyRequestStatus.PENDING_EXTERNAL,
  PrivacyRequestStatus.REQUIRES_INPUT,
]);

const FORCE_CLOSE_REJECTED_STATUSES = new Set<string>([
  PrivacyRequestStatus.COMPLETE,
  PrivacyRequestStatus.DENIED,
  PrivacyRequestStatus.CANCELED,
]);

interface JiraTicketRowProps {
  ticket: JiraTicketResult;
  onRetry: () => void;
  onRefresh: () => void;
  isRetrying: boolean;
  isRefreshing: boolean;
}

const JiraTicketRow = ({
  ticket,
  onRetry,
  onRefresh,
  isRetrying,
  isRefreshing,
}: JiraTicketRowProps) => (
  <Flex justify="space-between" align="center" gap={8}>
    <Flex align="center" gap={8} className="min-w-0">
      <Typography.Link
        href={ticket.ticket_url || undefined}
        target="_blank"
        rel="noopener noreferrer"
        data-testid={`jira-ticket-link-${ticket.ticket_key}`}
      >
        {ticket.ticket_key}
      </Typography.Link>
      <Tag
        color={getStatusColor(ticket.status)}
        data-testid={`jira-ticket-status-${ticket.ticket_key}`}
      >
        {ticket.status}
      </Tag>
    </Flex>
    <Flex gap={4} className="shrink-0">
      <Tooltip title="Retry ticket creation">
        <Button
          size="small"
          icon={<Icons.Undo />}
          onClick={onRetry}
          loading={isRetrying}
          disabled={
            ticket.instance_status !== StatusType.FAILED || isRefreshing
          }
          data-testid={`jira-ticket-retry-${ticket.ticket_key}`}
          aria-label="Retry ticket creation"
        />
      </Tooltip>
      <Tooltip title="Refresh ticket status">
        <Button
          size="small"
          icon={<Icons.Renew />}
          onClick={onRefresh}
          loading={isRefreshing}
          disabled={isRetrying}
          data-testid={`jira-ticket-refresh-${ticket.ticket_key}`}
          aria-label="Refresh ticket status"
        />
      </Tooltip>
    </Flex>
  </Flex>
);

interface RequestJiraTicketsProps {
  subjectRequest: PrivacyRequestEntity;
}

const RequestJiraTickets = ({ subjectRequest }: RequestJiraTicketsProps) => {
  const [isLinkModalOpen, setIsLinkModalOpen] = useState(false);
  const [isForceCloseModalOpen, setIsForceCloseModalOpen] = useState(false);
  const message = useMessage();

  const { data: tickets, isLoading } = useGetJiraTicketsQuery({
    privacy_request_id: subjectRequest.id,
  });

  const [retryJiraTicket, { isLoading: isRetrying, originalArgs: retryArgs }] =
    useRetryJiraTicketMutation();
  const [
    refreshJiraTicket,
    { isLoading: isRefreshing, originalArgs: refreshArgs },
  ] = useRefreshJiraTicketMutation();

  const handleRetry = async (ticket: JiraTicketResult) => {
    if (!ticket.instance_id) {
      return;
    }
    try {
      await retryJiraTicket({
        privacy_request_id: subjectRequest.id,
        instance_id: ticket.instance_id,
      }).unwrap();
      message.success(
        `Jira ticket ${ticket.ticket_key} creation retried successfully.`,
      );
    } catch (error) {
      message.error(
        getErrorMessage(
          error as RTKErrorResult["error"],
          `Failed to retry Jira ticket ${ticket.ticket_key} creation.`,
        ),
      );
    }
  };

  const handleRefresh = async (ticket: JiraTicketResult) => {
    if (!ticket.instance_id) {
      return;
    }
    try {
      await refreshJiraTicket({
        privacy_request_id: subjectRequest.id,
        instance_id: ticket.instance_id,
      }).unwrap();
      message.success(`Jira ticket ${ticket.ticket_key} status refreshed.`);
    } catch (error) {
      message.error(
        getErrorMessage(
          error as RTKErrorResult["error"],
          `Failed to refresh Jira ticket ${ticket.ticket_key} status.`,
        ),
      );
    }
  };

  return (
    <div className="mt-6">
      <div className="mb-4">
        <Title level={3}>Jira tickets</Title>
      </div>

      {isLoading ? (
        <Spin rootClassName="my-12" />
      ) : (
        <Flex vertical gap={8}>
          {tickets && tickets.length > 0 ? (
            tickets.map((ticket) => (
              <JiraTicketRow
                key={ticket.ticket_id}
                ticket={ticket}
                onRetry={() => handleRetry(ticket)}
                onRefresh={() => handleRefresh(ticket)}
                isRetrying={
                  isRetrying && retryArgs?.instance_id === ticket.instance_id
                }
                isRefreshing={
                  isRefreshing &&
                  refreshArgs?.instance_id === ticket.instance_id
                }
              />
            ))
          ) : (
            <Typography.Text type="secondary">
              No Jira tickets linked.
            </Typography.Text>
          )}
        </Flex>
      )}

      <Flex gap={8} className="mt-4">
        <Button
          icon={<Icons.Add />}
          onClick={() => setIsLinkModalOpen(true)}
          disabled={!LINK_ALLOWED_STATUSES.has(subjectRequest.status)}
          data-testid="link-jira-ticket-btn"
        >
          Link ticket
        </Button>
        <Button
          danger
          onClick={() => setIsForceCloseModalOpen(true)}
          disabled={FORCE_CLOSE_REJECTED_STATUSES.has(subjectRequest.status)}
          data-testid="force-close-btn"
        >
          Force close
        </Button>
      </Flex>

      <LinkJiraTicketModal
        privacyRequestId={subjectRequest.id}
        isOpen={isLinkModalOpen}
        onClose={() => setIsLinkModalOpen(false)}
      />
      <ForceCloseModal
        privacyRequestId={subjectRequest.id}
        isOpen={isForceCloseModalOpen}
        onClose={() => setIsForceCloseModalOpen(false)}
      />
    </div>
  );
};

export default RequestJiraTickets;
