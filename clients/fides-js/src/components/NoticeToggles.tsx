import { h } from "preact";

import { ConsentMechanism, PrivacyNotice } from "../lib/consent-types";
import Toggle from "./Toggle";
import Divider from "./Divider";
import { useDisclosure } from "../lib/hooks";

const NoticeToggle = ({
  notice,
  checked,
  onToggle,
}: {
  notice: PrivacyNotice;
  checked: boolean;
  onToggle: (noticeKey: PrivacyNotice["notice_key"]) => void;
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
          {notice.name}
        </span>
        <Toggle
          name={notice.name || ""}
          id={notice.notice_key}
          checked={checked}
          onChange={onToggle}
          disabled={notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY}
        />
      </div>
      <p {...getDisclosureProps()}>{notice.description}</p>
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
        const checked =
          notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY
            ? true
            : enabledNoticeKeys.indexOf(notice.notice_key) !== -1;
        const isLast = idx === notices.length - 1;
        return (
          <div>
            <NoticeToggle
              notice={notice}
              checked={checked}
              onToggle={handleToggle}
            />
            {!isLast ? <Divider /> : null}
          </div>
        );
      })}
    </div>
  );
};

export default NoticeToggles;
