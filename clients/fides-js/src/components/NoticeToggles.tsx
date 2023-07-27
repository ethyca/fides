import { ComponentChildren, VNode, h } from "preact";

import { ConsentMechanism, PrivacyNotice } from "../lib/consent-types";
import Toggle from "./Toggle";
import Divider from "./Divider";
import { useDisclosure } from "../lib/hooks";
import { GpcBadgeForNotice } from "./GpcBadge";

interface DataUse {
  key: string;
  name?: string;
}

export const DataUseToggle = ({
  dataUse,
  checked,
  onToggle,
  children,
  badge,
  gpcBadge,
  disabled,
}: {
  dataUse: DataUse;
  checked: boolean;
  onToggle: (noticeKey: DataUse["key"]) => void;
  children: ComponentChildren;
  badge?: string;
  gpcBadge?: VNode;
  disabled?: boolean;
}) => {
  const {
    isOpen,
    getButtonProps,
    getDisclosureProps,
    onToggle: toggleDescription,
  } = useDisclosure({
    id: dataUse.key,
  });

  const handleKeyDown = (event: KeyboardEvent) => {
    if (event.code === "Space" || event.code === "Enter") {
      toggleDescription();
    }
  };

  return (
    <div
      className={
        isOpen
          ? "fides-notice-toggle fides-notice-toggle-expanded"
          : "fides-notice-toggle"
      }
    >
      <div key={dataUse.key} className="fides-notice-toggle-title">
        <span
          role="button"
          tabIndex={0}
          onKeyDown={handleKeyDown}
          {...getButtonProps()}
          className="fides-notice-toggle-trigger"
        >
          <span className="fides-flex-center">
            {dataUse.name}
            {badge ? <span className="fides-notice-badge">{badge}</span> : null}
          </span>
          {gpcBadge}
        </span>

        <Toggle
          name={dataUse.name || ""}
          id={dataUse.key}
          checked={checked}
          onChange={onToggle}
          disabled={disabled}
        />
      </div>
      <div {...getDisclosureProps()}>{children}</div>
    </div>
  );
};

const NoticeToggles = ({
  notices,
  enabledNoticeKeys,
  onChange,
}: {
  notices: PrivacyNotice[];
  enabledNoticeKeys: Array<PrivacyNotice["notice_key"]>;
  onChange: (keys: Array<PrivacyNotice["notice_key"]>) => void;
}) => {
  const handleToggle = (noticeKey: PrivacyNotice["notice_key"]) => {
    // Add the notice to list of enabled notices
    if (enabledNoticeKeys.indexOf(noticeKey) === -1) {
      onChange([...enabledNoticeKeys, noticeKey]);
    }
    // Remove the notice from the list of enabled notices
    else {
      onChange(enabledNoticeKeys.filter((n) => n !== noticeKey));
    }
  };

  return (
    <div>
      {notices.map((notice, idx) => {
        const checked = enabledNoticeKeys.indexOf(notice.notice_key) !== -1;
        const isLast = idx === notices.length - 1;
        const dataUse = { key: notice.notice_key, name: notice.name };
        return (
          <div>
            <DataUseToggle
              dataUse={dataUse}
              checked={checked}
              onToggle={handleToggle}
              gpcBadge={<GpcBadgeForNotice notice={notice} value={checked} />}
              disabled={
                notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY
              }
            >
              {notice.description}
            </DataUseToggle>
            {!isLast ? <Divider /> : null}
          </div>
        );
      })}
    </div>
  );
};

export default NoticeToggles;
