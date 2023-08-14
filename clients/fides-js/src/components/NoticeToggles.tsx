import { ComponentChildren, h } from "preact";

import { ConsentMechanism, PrivacyNotice } from "../lib/consent-types";
import Toggle from "./Toggle";
import Divider from "./Divider";
import { useDisclosure } from "../lib/hooks";
import { GpcBadgeForNotice } from "./GpcBadge";

export const NoticeToggle = ({
  notice,
  checked,
  onToggle,
  children,
  badge,
}: {
  notice: PrivacyNotice;
  checked: boolean;
  onToggle: (noticeKey: PrivacyNotice["notice_key"]) => void;
  children: ComponentChildren;
  badge?: string;
}) => {
  const {
    isOpen,
    getButtonProps,
    getDisclosureProps,
    onToggle: toggleDescription,
  } = useDisclosure({
    id: notice.notice_key,
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
      <div key={notice.notice_key} className="fides-notice-toggle-title">
        <span
          role="button"
          tabIndex={0}
          onKeyDown={handleKeyDown}
          {...getButtonProps()}
          className="fides-notice-toggle-trigger"
        >
          <span className="fides-flex-center">
            {notice.name}
            {badge ? <span className="fides-notice-badge">{badge}</span> : null}
          </span>
          <GpcBadgeForNotice notice={notice} value={checked} />
        </span>

        <Toggle
          name={notice.name || ""}
          id={notice.notice_key}
          checked={checked}
          onChange={onToggle}
          disabled={notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY}
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
        return (
          <div>
            <NoticeToggle
              notice={notice}
              checked={checked}
              onToggle={handleToggle}
            >
              {notice.description}
            </NoticeToggle>
            {!isLast ? <Divider /> : null}
          </div>
        );
      })}
    </div>
  );
};

export default NoticeToggles;
