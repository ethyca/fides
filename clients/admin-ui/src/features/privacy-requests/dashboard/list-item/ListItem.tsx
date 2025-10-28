import {
  AntFlex as Flex,
  AntList as List,
  AntTag as Tag,
  formatIsoLocation,
  isoStringToEntry,
} from "fidesui";
import { isArray, toString } from "lodash";
import React from "react";

import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

import { RequestTableActions } from "../../RequestTableActions";
import {
  getCustomFields,
  getOtherIdentities,
  getPrimaryIdentity,
} from "../utils";
import {
  DaysLeft,
  Header,
  LabeledTag,
  LabeledText,
  PolicyActionTypes,
  ReceivedOn,
  ViewButton,
} from "./components";

interface ListItemProps {
  item: PrivacyRequestEntity;
  checkbox?: React.ReactNode;
}

export const ListItem = ({ item, checkbox }: ListItemProps) => {
  const primaryIdentity = getPrimaryIdentity(item.identity);
  const otherIdentities = getOtherIdentities(item.identity, primaryIdentity);
  const customFields = getCustomFields(item.custom_privacy_request_fields);

  const hasExtraDetails: boolean =
    otherIdentities.length > 0 || customFields.length > 0 || !!item.location;

  const locationIsoEntry = item.location
    ? (() => {
        try {
          return isoStringToEntry(item.location);
        } catch {
          return undefined;
        }
      })()
    : undefined;

  return (
    <List.Item>
      <div className="pr-4">{checkbox}</div>
      <div className="grow pr-8">
        <Header privacyRequest={item} />
        <Flex vertical gap="small" wrap className="pt-1">
          <Flex gap="small" wrap>
            {primaryIdentity && (
              <LabeledText label={primaryIdentity.label}>
                {primaryIdentity.value}
              </LabeledText>
            )}
            <PolicyActionTypes rules={item.policy.rules} />
            <Tag>{item.source}</Tag>
          </Flex>

          {hasExtraDetails && (
            <Flex wrap gap="middle">
              {item.location && (
                <LabeledTag key="location" label="Location">
                  {locationIsoEntry
                    ? formatIsoLocation({
                        isoEntry: locationIsoEntry,
                        showFlag: true,
                      })
                    : item.location}
                </LabeledTag>
              )}
              {otherIdentities.map((identity) => (
                <LabeledTag key={identity.key} label={identity.label}>
                  {identity.value}
                </LabeledTag>
              ))}
              {customFields.map((field) => (
                <LabeledText key={field.key} label={field.label}>
                  {isArray(field.value)
                    ? field.value.join(" - ")
                    : toString(field.value)}
                </LabeledText>
              ))}
            </Flex>
          )}
        </Flex>
      </div>
      <div className="flex shrink-0 flex-col items-end gap-2 pr-2 2xl:flex-row 2xl:gap-4">
        <ReceivedOn createdAt={item.created_at} />
        <DaysLeft
          daysLeft={item.days_left}
          status={item.status}
          timeframe={item.policy.execution_timeframe}
        />
      </div>
      <Flex className="min-w-[125px]" align="center" justify="end" gap="small">
        <ViewButton key="view" id={item.id} />
        <RequestTableActions key="other-actions" subjectRequest={item} />
      </Flex>
    </List.Item>
  );
};
