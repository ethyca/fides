import { h, VNode } from "preact";

import { PrivacyNoticeTranslation } from "../../lib/consent-types";
import { FidesServingToggleDetails } from "../../lib/events";
import { DEFAULT_LOCALE, getCurrentLocale } from "../../lib/i18n";
import { useI18n } from "../../lib/i18n/i18n-context";
import DataUseToggle from "../DataUseToggle";

export type RecordListType =
  | "purposes" // Sometimes includes custom purposes
  | "specialPurposes"
  | "features"
  | "specialFeatures"
  | "vendors";

export interface RecordListItem {
  id: string | number;
  name?: string;
  bestTranslation?: PrivacyNoticeTranslation | null; // only used for custom purposes
  disabled?: boolean; // only used for custom purposes
}

interface Props<T extends RecordListItem> {
  items: T[];
  type: RecordListType;
  title: string;
  enabledIds: string[];
  renderToggleChild?: (item: T, isCustomPurpose?: boolean) => VNode;
  onToggle: (
    payload: string[],
    item: T,
    toggleDetails: FidesServingToggleDetails,
  ) => void;
  renderBadgeLabel?: (item: T) => string | undefined;
  hideToggles?: boolean;
}

const RecordsList = <T extends RecordListItem>({
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

  const handleToggle = (item: T, toggleDetails: FidesServingToggleDetails) => {
    const purposeId = `${item.id}`;
    if (enabledIds.indexOf(purposeId) !== -1) {
      onToggle(
        enabledIds.filter((e) => e !== purposeId),
        item,
        toggleDetails,
      );
    } else {
      onToggle([...enabledIds, purposeId], item, toggleDetails);
    }
  };

  // Only show the toggle labels ("On"/"Off") in English, since our Toggle components are fixed-width!
  let toggleOnLabel: string | undefined;
  let toggleOffLabel: string | undefined;
  if (getCurrentLocale(i18n) === DEFAULT_LOCALE) {
    toggleOnLabel = "On";
    toggleOffLabel = "Off";
  }

  const getNameForItem = (item: RecordListItem) => {
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
          title={item.bestTranslation?.title || getNameForItem(item)}
          noticeKey={`${item.id}`}
          onToggle={(_, extraDetails) => {
            handleToggle(item, extraDetails);
          }}
          checked={enabledIds.indexOf(`${item.id}`) !== -1}
          badge={renderBadgeLabel ? renderBadgeLabel(item) : undefined}
          includeToggle={!hideToggles}
          onLabel={toggleOnLabel}
          offLabel={toggleOffLabel}
          disabled={item.disabled}
        >
          {renderToggleChild
            ? renderToggleChild(item, Boolean(item.bestTranslation))
            : ""}
        </DataUseToggle>
      ))}
    </div>
  );
};

export default RecordsList;
