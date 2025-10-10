import { AntFlex as Flex, AntList as List } from "fidesui";
import React from "react";

import RequestStatusBadge from "~/features/common/RequestStatusBadge";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

import { RequestTableActions } from "../RequestTableActions";
import { DaysLeft } from "./DaysLeft";
import { EmailIdentity, NonEmailIdentities } from "./identities";
import { ViewButton } from "./listButtons";
import { PolicyActionTypes } from "./PolicyActionTypes";
import { RequestTitle } from "./RequestTitle";
import { ReceivedOn } from "./RevievedOn";

interface PrivacyRequestListItemProps {
  item: PrivacyRequestEntity;
}

export const PrivacyRequestListItem = ({
  item,
}: PrivacyRequestListItemProps) => (
  <List.Item>
    <List.Item.Meta
      title={
        <Flex gap={16} wrap align="center">
          <RequestTitle id={item.id} policyName={item.policy.name} />
          <RequestStatusBadge status={item.status} />
        </Flex>
      }
      description={
        <div className="pt-1">
          <Flex vertical gap={16} wrap>
            <Flex gap={8} wrap>
              <EmailIdentity value={item.identity.email?.value} />
              <PolicyActionTypes rules={item.policy.rules} />
            </Flex>

            <Flex wrap gap={16}>
              <NonEmailIdentities identities={item.identity} />
            </Flex>
          </Flex>
        </div>
      }
    />
    <div className="pr-2">
      <Flex gap={16} wrap>
        <ReceivedOn createdAt={item.created_at} />
        <DaysLeft
          daysLeft={item.days_left}
          status={item.status}
          timeframe={item.policy.execution_timeframe}
        />
      </Flex>
    </div>
    <div className="flex min-w-[125px] items-center justify-end gap-2">
      <ViewButton key="view" id={item.id} />
      <RequestTableActions key="other-actions" subjectRequest={item} />
    </div>
  </List.Item>
);
