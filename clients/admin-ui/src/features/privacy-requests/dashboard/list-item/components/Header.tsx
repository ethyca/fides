import {
  AntFlex as Flex,
  AntTooltip as Tooltip,
  AntTypography as Typography,
  Icons,
} from "fidesui";
import { useRouter } from "next/router";
import React from "react";

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
              router.push(`/privacy-requests/${privacyRequest.id}`);
            }}
            copyable={{
              text: privacyRequest.id,
              icon: (
                <Tooltip title="Copy request ID">
                  <div className="mt-1">
                    <Icons.Copy />
                  </div>
                </Tooltip>
              ),
              tooltips: null,
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
