import { AntFlex as Flex, AntTypography as Typography, Icons } from "fidesui";
import { useRouter } from "next/router";
import React from "react";

import { PRIVACY_REQUEST_DETAIL_ROUTE } from "~/features/common/nav/routes";
import RequestStatusBadge from "~/features/common/RequestStatusBadge";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

interface HeaderProps {
  privacyRequest: PrivacyRequestEntity;
}

export const Header = ({ privacyRequest }: HeaderProps) => {
  const router = useRouter();

  return (
    <Flex gap={16} wrap align="center">
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
            copyable={{
              text: privacyRequest.id,
              icon: (
                <Icons.Copy className="size-3.5 text-[var(--ant-color-text-secondary)]" />
              ),
              tooltips: ["Copy request ID", "Copied"],
            }}
          >
            {privacyRequest.policy.name}
          </Typography.Link>
        </Typography.Title>
      </div>
      <RequestStatusBadge status={privacyRequest.status} />
    </Flex>
  );
};
