/** @jsx createElement */
import { createElement } from "react";

import { PrivacyNotice } from "../lib/consent-types";
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
        isOpen ? "notice-toggle notice-toggle-expanded" : "notice-toggle"
      }
    >
      <div key={notice.notice_key} className="notice-toggle-title">
        <span
          role="button"
          tabIndex={0}
          onKeyDown={handleKeyDown}
          // eslint-disable-next-line react/jsx-props-no-spreading
          {...getButtonProps()}
          className="notice-toggle-trigger"
        >
          {notice.name}
        </span>
        <Toggle
          name={notice.name || ""}
          id={notice.notice_key}
          checked={checked}
          onChange={onToggle}
        />
      </div>
      {/* eslint-disable-next-line react/jsx-props-no-spreading */}
      <p {...getDisclosureProps()}>{notice.description}</p>
    </div>
  );
};

/**
 * A React component (not Preact!!) to render notices and their toggles
 *
 * We use React instead of Preact so that this component can be shared with
 * the Privacy Center React app.
 */
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
            />
            {!isLast ? <Divider /> : null}
          </div>
        );
      })}
    </div>
  );
};

export default NoticeToggles;
