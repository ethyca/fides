/** @jsx createElement */
import { createElement } from "react";

import { PrivacyNotice } from "../lib/consent-types";
import Toggle from "./Toggle";

/**
 * A React component (not Preact!!) to render notices and their toggles
 *
 * We use React instead of Preact so that this component can be shared with
 * the Privacy Center React app.
 */
const NoticeToggleTable = ({
  notices,
  enabledNoticeIds,
  onChange,
}: {
  notices: PrivacyNotice[];
  enabledNoticeIds: Array<PrivacyNotice["id"]>;
  onChange: (ids: Array<PrivacyNotice["id"]>) => void;
}) => {
  const handleToggle = (noticeId: PrivacyNotice["id"]) => {
    // Add the notice to list of enabled notices
    if (enabledNoticeIds.indexOf(noticeId) === -1) {
      onChange([...enabledNoticeIds, noticeId]);
    }
    // Remove the notice from the list of enabled notices
    else {
      onChange(enabledNoticeIds.filter((n) => n !== noticeId));
    }
  };

  return (
    <div>
      {notices.map((notice) => {
        const checked = enabledNoticeIds.indexOf(notice.id) !== -1;
        return (
          <div
            key={notice.id}
            style={{ display: "flex", justifyContent: "space-between" }}
          >
            <span>{notice.name}</span>
            <Toggle
              name={notice.name}
              id={notice.id}
              checked={checked}
              onChange={handleToggle}
            />
          </div>
        );
      })}
    </div>
  );
};

export default NoticeToggleTable;
