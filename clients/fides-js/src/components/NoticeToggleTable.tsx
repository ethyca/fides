import { h } from "preact";
import { PrivacyNotice } from "../lib/consent-types";
import Toggle from "./Toggle";

/**
 * A React component (not Preact!!) to render notices and their toggles
 *
 * We use React instead of Preact so that this component can be shared with
 * the Privacy Center React app.
 */
const NoticeToggleTable = ({ notices }: { notices: PrivacyNotice[] }) => (
  <div>
    {notices.map((notice) => (
      <div
        key={notice.id}
        style={{ display: "flex", justifyContent: "space-between" }}
      >
        <span>{notice.name}</span>
        {/* TODO: CSS to make this look like an actual switch */}
        <Toggle name={notice.name} />
      </div>
    ))}
  </div>
);

export default NoticeToggleTable;
