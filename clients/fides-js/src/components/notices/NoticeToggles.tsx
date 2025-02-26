import { h } from "preact";

import { GpcStatus } from "../../lib/consent-types";
import { DEFAULT_LOCALE, getCurrentLocale } from "../../lib/i18n";
import { useI18n } from "../../lib/i18n/i18n-context";
import DataUseToggle from "../DataUseToggle";
import Divider from "../Divider";
import { GpcBadge } from "../GpcBadge";

export interface NoticeToggleProps {
  noticeKey: string;
  title: string;
  description?: string;
  checked: boolean;
  disabled: boolean;
  gpcStatus: GpcStatus;
}

export const NoticeToggles = ({
  noticeToggles,
  enabledNoticeKeys,
  onChange,
}: {
  noticeToggles: NoticeToggleProps[];
  enabledNoticeKeys: Array<string>;
  onChange: (keys: Array<string>) => void;
}) => {
  const { i18n } = useI18n();
  const handleToggle = (noticeKey: string) => {
    // Add the notice to list of enabled notices
    if (enabledNoticeKeys.indexOf(noticeKey) === -1) {
      onChange([...enabledNoticeKeys, noticeKey]);
    }
    // Remove the notice from the list of enabled notices
    else {
      onChange(enabledNoticeKeys.filter((n) => n !== noticeKey));
    }
  };

  // Only show the toggle labels ("On"/"Off") in English, since our Toggle components are fixed-width!
  let toggleOnLabel: string | undefined;
  let toggleOffLabel: string | undefined;
  if (getCurrentLocale(i18n) === DEFAULT_LOCALE) {
    toggleOnLabel = "On";
    toggleOffLabel = "Off";
  }

  return (
    <div>
      {noticeToggles.map((props, idx) => {
        const { noticeKey, title, description, checked, disabled, gpcStatus } =
          props;
        const isLast = idx === noticeToggles.length - 1;
        return (
          <div key={noticeKey}>
            <DataUseToggle
              noticeKey={noticeKey}
              title={title}
              checked={checked}
              onToggle={handleToggle}
              gpcBadge={<GpcBadge status={gpcStatus} />}
              disabled={disabled}
              onLabel={toggleOnLabel}
              offLabel={toggleOffLabel}
            >
              {description}
            </DataUseToggle>
            {!isLast ? <Divider /> : null}
          </div>
        );
      })}
    </div>
  );
};

export default NoticeToggles;
