import {
  Button,
  CUSTOM_TAG_COLOR,
  Flex,
  Icons,
  PageSpinner,
  Tag,
  Title,
  Tooltip,
  Typography,
} from "fidesui";
import { useState } from "react";

import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

import LinkJiraTicketModal from "./LinkJiraTicketModal";
import { useGetJiraTicketsQuery } from "./privacy-request-jira-tickets.slice";
import { JiraTicketResult } from "./types";

const statusColorMap: Record<string, CUSTOM_TAG_COLOR> = {
  done: CUSTOM_TAG_COLOR.SUCCESS,
  "in progress": CUSTOM_TAG_COLOR.CAUTION,
  "to do": CUSTOM_TAG_COLOR.INFO,
};

const getStatusColor = (status: string): CUSTOM_TAG_COLOR =>
  statusColorMap[status.toLowerCase()] ?? CUSTOM_TAG_COLOR.DEFAULT;

const JiraTicketRow = ({ ticket }: { ticket: JiraTicketResult }) => (
  <Flex justify="space-between" align="center" gap={8}>
    <Flex align="center" gap={8} className="min-w-0">
      <Typography.Link
        href={ticket.ticket_url}
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
      <Tooltip title="Retry not yet available">
        <Button
          size="small"
          icon={<Icons.Undo />}
          disabled
          data-testid={`jira-ticket-retry-${ticket.ticket_key}`}
          aria-label="Retry ticket creation"
        />
      </Tooltip>
      <Tooltip title="Refresh not yet available">
        <Button
          size="small"
          icon={<Icons.Renew />}
          disabled
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

  const { data: tickets, isLoading } = useGetJiraTicketsQuery({
    privacy_request_id: subjectRequest.id,
  });

  return (
    <div className="mt-6">
      <div className="mb-4">
        <Title level={3}>Jira tickets</Title>
      </div>

      {isLoading ? (
        <PageSpinner alignment="start" />
      ) : (
        <Flex vertical gap={8}>
          {tickets && tickets.length > 0 ? (
            tickets.map((ticket) => (
              <JiraTicketRow key={ticket.ticket_id} ticket={ticket} />
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
          data-testid="link-jira-ticket-btn"
        >
          Link ticket
        </Button>
        <Tooltip title="Force close not yet available">
          <Button danger disabled data-testid="force-close-btn">
            Force close
          </Button>
        </Tooltip>
      </Flex>

      <LinkJiraTicketModal
        privacyRequestId={subjectRequest.id}
        isOpen={isLinkModalOpen}
        onClose={() => setIsLinkModalOpen(false)}
      />
    </div>
  );
};

export default RequestJiraTickets;
