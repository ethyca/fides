import { h } from "preact";
import { PrivacyNotice } from "../lib/consent-types";

const NoticeToggleTable = ({ notices }: { notices: PrivacyNotice[] }) => {
  console.log("table", notices);

  return (
    <div>
      {notices.map((notice) => {
        return <p key={notice.id}>{notice.name}</p>;
      })}
    </div>
  );
};

export default NoticeToggleTable;
