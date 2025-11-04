import { AntFlex as Flex, AntTypography as Typography, Icons } from "fidesui";
import { useRouter } from "next/router";
import React from "react";

import { PRIVACY_REQUEST_DETAIL_ROUTE } from "~/features/common/nav/routes";
import RequestStatusBadge from "~/features/common/RequestStatusBadge";
import { SubjectRequestActionTypeMap } from "~/features/privacy-requests/constants";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

interface HeaderProps {
  privacyRequest: PrivacyRequestEntity;
}

export const Header = ({ privacyRequest }: HeaderProps) => {
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
            {/*
            Convert different action types to a single string
            (e.g. "Access/Erasure request"
            */}
            {privacyRequest.policy.rules
              .map((rule) => SubjectRequestActionTypeMap.get(rule.action_type))
              .join("/")}{" "}
            request
          </Typography.Link>
        </Typography.Title>
      </div>
      <RequestStatusBadge status={privacyRequest.status} />
      <Typography.Text
        type="secondary"
        copyable={{
          text: privacyRequest.id,
          icon: (
            <div className="size-4">
              <Icons.Copy className="size-4 text-[var(--ant-color-text-secondary)]" />
            </div>
          ),
          tooltips: ["Copy request ID", "Copied"],
        }}
      >
        {privacyRequest.id}
      </Typography.Text>
    </Flex>
  );
};
