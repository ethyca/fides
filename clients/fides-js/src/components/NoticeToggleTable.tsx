/** @jsx React */

import React from "react";
import { PrivacyNotice } from "../lib/consent-types";

/**
 * A React component (not Preact!!) to render notices and their toggles
 *
 * We use React instead of Preact so that this component can be shared with
 * the Privacy Center React app.
 */
const NoticeToggleTable = ({ notices }: { notices: PrivacyNotice[] }) => {
  console.log("table", notices);

  return (
    <div>
      {notices.map((notice) => {
        return (
          <div
            key={notice.id}
            style={{ display: "flex", justifyContent: "space-between" }}
          >
            <span>{notice.name}</span>
            {/* TODO: CSS to make this look like an actual switch */}
            <label>
              <input type="checkbox" />
            </label>
          </div>
        );
      })}
    </div>
  );
};

export default NoticeToggleTable;
