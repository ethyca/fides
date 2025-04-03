import { AntTag as Tag } from "fidesui";
import { useState } from "react";

import { formatDate } from "~/features/common/utils";

import styles from "./ActivityTimelineEntry.module.scss";

interface ActivityTimelineEntryProps {
  author: string;
  title: string;
  timestamp: string;
  type: string;
  content?: React.ReactNode;
  logs?: React.ReactNode;
  className?: string;
}

const ActivityTimelineEntry = ({
  author,
  timestamp,
  title,
  type,
  content,
  logs,
  className = "",
}: ActivityTimelineEntryProps) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div
      className={`${styles.container} ${isOpen ? styles["container--open"] : undefined} ${className}`}
    >
      <button
        type="button"
        className={styles.header}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className={styles.author}>{author}:</span>
        <span className={styles.title}>{title}</span>
        <span className={styles.timestamp}>{formatDate(timestamp)}</span>
        <Tag>{type}</Tag>
        <span className={styles.viewLogs}>{isOpen ? "Hide" : "View"} logs</span>
      </button>
      {content && <span className={styles.content}>{content}</span>}
      <div
        className={`${styles.logs} ${isOpen ? styles["logs--open"] : undefined}`}
      >
        {logs}
      </div>
    </div>
  );
};
export default ActivityTimelineEntry;
