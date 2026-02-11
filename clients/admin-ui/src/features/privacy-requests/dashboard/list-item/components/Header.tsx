import { CopyTooltip, Flex, Tag, Typography } from "fidesui";
import { useRouter } from "next/router";
import React from "react";

import { PRIVACY_REQUEST_DETAIL_ROUTE } from "~/features/common/nav/routes";
import RequestStatusBadge from "~/features/common/RequestStatusBadge";
import { SubjectRequestActionTypeMap } from "~/features/privacy-requests/constants";
import { PrivacyRequestResponse } from "~/types/api";

import { getUniqueActionTypes, IdentityValueWithKey } from "../../utils";

interface HeaderProps {
  privacyRequest: PrivacyRequestResponse;
  primaryIdentity: IdentityValueWithKey | null;
}

export const Header = ({ privacyRequest, primaryIdentity }: HeaderProps) => {
  const router = useRouter();

  const uniqueActionTypes = privacyRequest.policy.rules
    ? getUniqueActionTypes(privacyRequest.policy.rules)
    : [];

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
      {uniqueActionTypes.length > 0 && (
        <Flex gap={4}>
          {uniqueActionTypes.map((actionType) => (
            <Tag key={actionType}>
              {SubjectRequestActionTypeMap.get(actionType)}
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
