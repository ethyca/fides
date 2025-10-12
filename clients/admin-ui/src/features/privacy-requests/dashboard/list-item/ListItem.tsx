import { AntFlex as Flex, AntList as List, AntTag as Tag } from "fidesui";
import React from "react";

import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

import { RequestTableActions } from "../../RequestTableActions";
import {
  DaysLeft,
  EmailIdentity,
  Header,
  NonEmailIdentities,
  PolicyActionTypes,
  ReceivedOn,
  ViewButton,
} from "./components";

interface ListItemProps {
  item: PrivacyRequestEntity;
}

export const ListItem = ({ item }: ListItemProps) => (
  <List.Item>
    <div className="grow">
      <Header privacyRequest={item} />
      <Flex vertical gap={16} wrap className="pt-1">
        <Flex gap={8} wrap>
          <EmailIdentity value={item.identity.email?.value} />
          <PolicyActionTypes rules={item.policy.rules} />
          <Tag>{item.source}</Tag>
        </Flex>

        <Flex wrap gap={16}>
          <NonEmailIdentities identities={item.identity} />
        </Flex>
      </Flex>
    </div>
    <Flex gap={16} wrap className="pr-2">
      <ReceivedOn createdAt={item.created_at} />
      <DaysLeft
        daysLeft={item.days_left}
        status={item.status}
        timeframe={item.policy.execution_timeframe}
      />
    </Flex>
    <Flex className="min-w-[125px]" align="center" justify="end" gap={8}>
      <ViewButton key="view" id={item.id} />
      <RequestTableActions key="other-actions" subjectRequest={item} />
    </Flex>
  </List.Item>
);
