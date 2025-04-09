import classNames from "classnames";
import { AntList as List, AntTag as Tag } from "fidesui";
import { map } from "lodash";
import { useCallback } from "react";

import { formatDate } from "~/features/common/utils";
import { ExecutionLogStatus } from "~/types/api";

import { ExecutionLog, PrivacyRequestResults } from "../types";
import styles from "./ActivityTimelineCollapse.module.scss";

interface ActivityTimelineProps {
  results?: PrivacyRequestResults;
  onItemClicked: ({ key, logs }: { key: string; logs: ExecutionLog[] }) => void;
}

interface ActivityTimelineItem {
  logs: ExecutionLog[];
  key: string;
}

const ActivityTimelineCollapse = ({
  results,
  onItemClicked,
}: ActivityTimelineProps) => {
  const items: ActivityTimelineItem[] = map(results, (logs, key) => ({
    logs,
    key,
  }));

  const renderItem = useCallback(
    ({ logs, key }: ActivityTimelineItem) => {
      const hasUnresolvedError = logs.some(
        (log) => log.status === ExecutionLogStatus.ERROR,
      );
      const hasSkippedEntry = logs.some(
        (log) => log.status === ExecutionLogStatus.SKIPPED,
      );

      return (
        <List.Item
          key={key}
          className={classNames(styles.item, {
            [styles["item--error"]]: hasUnresolvedError,
          })}
          onClick={() => onItemClicked({ key, logs })}
        >
          <div className={styles.header}>
            <span className={styles.author}>Fides:</span>
            <span
              className={classNames(styles.title, {
                [styles["title--error"]]: hasUnresolvedError,
                [styles["title--skipped"]]: hasSkippedEntry,
              })}
            >
              {key}
              {hasUnresolvedError && " failed"}
            </span>
            <span className={styles.timestamp}>
              {formatDate(logs[0].updated_at)}
            </span>
            <Tag color="sandstone">Request update</Tag>
            {hasUnresolvedError ||
              (hasSkippedEntry && (
                <span className={styles.viewLogs}>View Log</span>
              ))}
          </div>
        </List.Item>
      );
    },
    [onItemClicked],
  );

  return (
    <List className={styles.collapse} bordered={false} split={false}>
      {items.map(renderItem)}
    </List>
  );
};

export default ActivityTimelineCollapse;
