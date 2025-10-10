import { AntFlex as Flex, AntList as List } from "fidesui";
import React from "react";

import RequestStatusBadge from "~/features/common/RequestStatusBadge";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

import { RequestTableActions } from "../../RequestTableActions";
import {
  DaysLeft,
  EmailIdentity,
  NonEmailIdentities,
  PolicyActionTypes,
  ReceivedOn,
  RequestTitle,
  ViewButton,
} from "./components";

interface ListItemProps {
  item: PrivacyRequestEntity;
}

export const ListItem = ({ item }: ListItemProps) => (
  <List.Item>
    <div className="grow">
      <Flex gap={16} wrap align="center">
        <RequestTitle id={item.id} policyName={item.policy.name} />
        <RequestStatusBadge status={item.status} />
      </Flex>
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
    </div>
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
