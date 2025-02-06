import { h, VNode } from "preact";

import { DEFAULT_LOCALE, getCurrentLocale } from "../../lib/i18n";
import { useI18n } from "../../lib/i18n/i18n-context";
import DataUseToggle from "../DataUseToggle";
import {PrivacyNoticeTranslation} from "~/lib/consent-types";

export type RecordListType =
  | "purposes"
  | "customPurposes"
  | "specialPurposes"
  | "features"
  | "specialFeatures"
  | "vendors";

interface Item {
  id: string | number;
  name?: string;
  bestTranslation?: PrivacyNoticeTranslation | null; // only used for custom purposes
}

interface Props<T extends Item> {
  items: T[];
  type: RecordListType;
  title: string;
  enabledIds: string[];
  renderToggleChild?: (item: T) => VNode;
  onToggle: (payload: string[]) => void;
  renderBadgeLabel?: (item: T) => string | undefined;
  hideToggles?: boolean;
}

const RecordsList = <T extends Item>({
  items,
  type,
  title,
  enabledIds,
  renderToggleChild,
  renderBadgeLabel,
  onToggle,
  hideToggles,
}: Props<T>) => {
  const { i18n } = useI18n();
  if (items.length === 0) {
    return null;
  }

  const handleToggle = (item: T) => {
    const purposeId = `${item.id}`;
    if (enabledIds.indexOf(purposeId) !== -1) {
      onToggle(enabledIds.filter((e) => e !== purposeId));
    } else {
      onToggle([...enabledIds, purposeId]);
    }
  };

  // Only show the toggle labels ("On"/"Off") in English, since our Toggle components are fixed-width!
  let toggleOnLabel: string | undefined;
  let toggleOffLabel: string | undefined;
  if (getCurrentLocale(i18n) === DEFAULT_LOCALE) {
    toggleOnLabel = "On";
    toggleOffLabel = "Off";
  }

  const getNameForItem = (item: Item) => {
    if (type === "vendors") {
      // Return the (non-localized!) name for vendors
      return item.name as string;
    }
    // Otherwise, return the localized name for purposes/features/etc.
    return i18n.t(`exp.tcf.${type}.${item.id}.name`);
  };

  return (
    <div data-testid={`records-list-${type}`}>
      <div className="fides-record-header">{title}</div>
      {items.map((item) => (
        <DataUseToggle
          key={item.id}
          title={
            item.bestTranslation
              ? item.bestTranslation.title || ""
              : getNameForItem(item)
          }
          noticeKey={`${item.id}`}
          onToggle={() => {
            handleToggle(item);
          }}
          checked={enabledIds.indexOf(`${item.id}`) !== -1}
          badge={renderBadgeLabel ? renderBadgeLabel(item) : undefined}
          includeToggle={!hideToggles}
          onLabel={toggleOnLabel}
          offLabel={toggleOffLabel}
        >
          {renderToggleChild ? renderToggleChild(item) : ""}
        </DataUseToggle>
      ))}
    </div>
  );
};

export default RecordsList;
