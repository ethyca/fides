import classNames from "classnames";
import { Flex, formatIsoLocation, isoStringToEntry, List } from "fidesui";
import { isArray } from "lodash";
import React from "react";

import { formatIsoDate } from "~/features/common/utils";
import { PrivacyRequestResponseExtended } from "~/types/api";

import { RequestTableActions } from "../../RequestTableActions";
import {
  getCustomFields,
  getOtherIdentities,
  getPrimaryIdentity,
} from "../utils";
import {
  DaysLeft,
  Header,
  HeaderLinkOverrides,
  LabeledText,
  ReceivedOn,
} from "./components";

interface ListItemProps {
  item: PrivacyRequestResponseExtended;
  checkbox?: React.ReactNode;
  showActions?: boolean;
  /**
   * When true, the days-left/received-on cluster always stacks vertically
   * regardless of viewport width. Use in narrow containers (e.g. drawers)
   * where the default `2xl:flex-row` viewport-driven media query is
   * misleading.
   */
  compact?: boolean;
  /**
   * Slot for header customization. Mirrors AntD's nested-config style
   * (e.g. `Table`'s `expandable` / `pagination` / `rowSelection` props) —
   * add sub-keys here as new header overrides become necessary, instead of
   * growing the top-level prop list.
   */
  header?: {
    link?: HeaderLinkOverrides;
    extraTags?: React.ReactNode;
  };
}

export const ListItem = ({
  item,
  checkbox,
  showActions = true,
  compact = false,
  header,
}: ListItemProps) => {
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
      {checkbox && <div className="pr-4">{checkbox}</div>}
      <Flex vertical gap="small" className="grow pr-8">
        <Header
          privacyRequest={item}
          primaryIdentity={primaryIdentity}
          link={header?.link}
          extraTags={header?.extraTags}
        />
        <Flex vertical gap="small" wrap>
          <Flex gap="small" wrap>
            <LabeledText label="Policy">{item.policy.name}</LabeledText>
            <LabeledText label="Source">{item.source}</LabeledText>
          </Flex>

          {hasExtraDetails && (
            <Flex wrap className="gap-x-3 gap-y-2">
              {item.location && (
                <LabeledText key="location" label="Location">
                  {locationIsoEntry
                    ? formatIsoLocation({
                        isoEntry: locationIsoEntry,
                        showFlag: true,
                      })
                    : item.location}
                </LabeledText>
              )}
              {otherIdentities.map((identity) => (
                <LabeledText
                  key={identity.key}
                  label={identity.label}
                  copyValue={formatIsoDate(identity.value)}
                >
                  {formatIsoDate(identity.value)}
                </LabeledText>
              ))}
              {customFields.map((field) => {
                const valueString = isArray(field.value)
                  ? field.value.join(" - ")
                  : formatIsoDate(field.value);
                return (
                  <LabeledText
                    key={field.key}
                    label={field.label}
                    copyValue={valueString}
                  >
                    {valueString}
                  </LabeledText>
                );
              })}
            </Flex>
          )}
        </Flex>
      </Flex>
      <Flex
        vertical
        className={classNames(
          "shrink-0 items-end gap-2 pr-2",
          !compact && "2xl:flex-row 2xl:gap-4",
        )}
      >
        <DaysLeft
          daysLeft={item.days_left}
          status={item.status}
          timeframe={item.policy.execution_timeframe}
        />
        <ReceivedOn createdAt={item.created_at} />
      </Flex>
      {showActions && (
        <Flex className="min-w-[90px]" align="center" justify="end" gap="small">
          <RequestTableActions key="other-actions" subjectRequest={item} />
        </Flex>
      )}
    </List.Item>
  );
};
