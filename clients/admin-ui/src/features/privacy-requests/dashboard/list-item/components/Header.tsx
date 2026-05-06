import { CopyTooltip, Flex, Tag, Typography } from "fidesui";
import { uniqBy } from "lodash";
import { useRouter } from "next/router";
import React from "react";

import { useFlags } from "~/features/common/features";
import { PRIVACY_REQUEST_DETAIL_ROUTE } from "~/features/common/nav/routes";
import RequestStatusBadge from "~/features/common/RequestStatusBadge";
import { SubjectRequestActionTypeMap } from "~/features/privacy-requests/constants";
import { PrivacyRequestResponseExtended } from "~/types/api";

import { IdentityValueWithKey } from "../../utils";

export type HeaderLinkOverrides = {
  /**
   * Anchor `target`. When set, the header link bypasses the in-app
   * `router.push` interceptor and lets the native anchor handle navigation —
   * use `"_blank"` to open in a new tab.
   */
  target?: React.HTMLAttributeAnchorTarget;
  /** Anchor `rel`. */
  rel?: string;
};

interface HeaderProps {
  privacyRequest: PrivacyRequestResponseExtended;
  primaryIdentity: IdentityValueWithKey | null;
  link?: HeaderLinkOverrides;
  /**
   * Optional element(s) rendered inline alongside the existing status / rule
   * tags. Use to mark a row with extra context like a "Current" tag in
   * embedded contexts.
   */
  extraTags?: React.ReactNode;
}

export const Header = ({
  privacyRequest,
  primaryIdentity,
  link,
  extraTags,
}: HeaderProps) => {
  const useNativeNavigation = link?.target !== undefined;
  const router = useRouter();
  const { flags } = useFlags();

  const uniqueRules = uniqBy(privacyRequest.policy.rules ?? [], "action_type");

  return (
    <Flex gap={12} wrap align="center">
      <div className="flex min-w-[100px] gap-2">
        <Typography.Title level={3}>
          <Typography.Link
            href={`/privacy-requests/${privacyRequest.id}`}
            variant="primary"
            target={link?.target}
            rel={link?.rel}
            onClick={
              useNativeNavigation
                ? undefined
                : (e) => {
                    e.preventDefault();
                    router.push({
                      pathname: PRIVACY_REQUEST_DETAIL_ROUTE,
                      query: { id: privacyRequest.id },
                    });
                  }
            }
          >
            {primaryIdentity?.value ?? "Unknown identity"}
          </Typography.Link>
        </Typography.Title>
      </div>
      <Flex gap="small" align="center">
        <RequestStatusBadge status={privacyRequest.status} />
        {uniqueRules.map((rule) => (
          <Tag key={rule.action_type}>
            {SubjectRequestActionTypeMap.get(rule.action_type)}
          </Tag>
        ))}
        {extraTags}
      </Flex>
      {/* Only the first ticket is shown — at most one Jira ticket per request is supported today */}
      {flags.jiraIntegration && privacyRequest.jira_tickets?.[0] && (
        <Flex gap={4} align="center">
          <Typography.Link
            href={privacyRequest.jira_tickets[0].ticket_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            {privacyRequest.jira_tickets[0].ticket_key}
          </Typography.Link>
          {privacyRequest.jira_tickets[0].status && (
            <Tag>{privacyRequest.jira_tickets[0].status}</Tag>
          )}
        </Flex>
      )}
      <CopyTooltip contentToCopy={privacyRequest.id}>
        <Typography.Text type="secondary">{privacyRequest.id}</Typography.Text>
      </CopyTooltip>
    </Flex>
  );
};
