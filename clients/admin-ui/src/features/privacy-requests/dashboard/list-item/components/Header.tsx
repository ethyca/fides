import {
  AntFlex as Flex,
  AntTag as Tag,
  AntTypography as Typography,
  CopyTooltip,
} from "fidesui";
import { useRouter } from "next/router";
import React from "react";

import { PRIVACY_REQUEST_DETAIL_ROUTE } from "~/features/common/nav/routes";
import RequestStatusBadge from "~/features/common/RequestStatusBadge";
import { SubjectRequestActionTypeMap } from "~/features/privacy-requests/constants";
import { PrivacyRequestResponse } from "~/types/api";

import { IdentityValueWithKey } from "../../utils";

interface HeaderProps {
  privacyRequest: PrivacyRequestResponse;
  primaryIdentity: IdentityValueWithKey | null;
}

export const Header = ({ privacyRequest, primaryIdentity }: HeaderProps) => {
  const router = useRouter();

  return (
    <Flex gap={12} wrap align="center">
      <div className="flex min-w-[100px] gap-2">
        <Typography.Title level={3}>
          <Typography.Link
            href={`/privacy-requests/${privacyRequest.id}`}
            variant="primary"
            onClick={(e) => {
              e.preventDefault();
              router.push({
                pathname: PRIVACY_REQUEST_DETAIL_ROUTE,
                query: { id: privacyRequest.id },
              });
            }}
          >
            {primaryIdentity?.value ?? "Unknown identity"}
          </Typography.Link>
        </Typography.Title>
      </div>
      <RequestStatusBadge status={privacyRequest.status} />
      {privacyRequest.policy.rules && (
        <Flex gap={4}>
          {privacyRequest.policy.rules.map((rule) => (
            <Tag key={rule.action_type}>
              {SubjectRequestActionTypeMap.get(rule.action_type)}
            </Tag>
          ))}
        </Flex>
      )}
      <CopyTooltip contentToCopy={privacyRequest.id}>
        <Typography.Text type="secondary">{privacyRequest.id}</Typography.Text>
      </CopyTooltip>
    </Flex>
  );
};
