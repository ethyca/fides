import classNames from "classnames";
import { AntList as List, AntTag as Tag } from "fidesui";
import { map } from "lodash";
import { useCallback } from "react";

import { formatDate } from "~/features/common/utils";
import { ExecutionLogStatus } from "~/types/api";

import { ExecutionLog, PrivacyRequestResults } from "../types";
import styles from "./ActivityTimelineList.module.scss";

interface ActivityTimelineItem {
  // eslint-disable-next-line react/no-unused-prop-types
  logs: ExecutionLog[];
  // eslint-disable-next-line react/no-unused-prop-types
  key: string;
}

interface ActivityTimelineProps {
  results?: PrivacyRequestResults;
  onItemClicked: ({ key, logs }: ActivityTimelineItem) => void;
}

const ActivityTimelineList = ({
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
        <button
          type="button"
          onClick={() => onItemClicked({ key, logs })}
          className={classNames(styles.itemButton, {
            [styles["itemButton--error"]]: hasUnresolvedError,
          })}
          data-testid="activity-timeline-item"
        >
          <div className={styles.header}>
            <span data-testid="activity-timeline-author">Fides:</span>
            <span
              className={classNames(styles.title, {
                [styles["title--error"]]: hasUnresolvedError,
                [styles["title--skipped"]]: hasSkippedEntry,
              })}
              data-testid="activity-timeline-title"
            >
              {key}
              {hasUnresolvedError && " failed"}
            </span>
            <span
              className={styles.timestamp}
              data-testid="activity-timeline-timestamp"
            >
              {formatDate(logs[0].updated_at)}
            </span>
            <Tag color="sandstone" data-testid="activity-timeline-type">
              Request update
            </Tag>
            {(hasUnresolvedError || hasSkippedEntry) && (
              <span
                className={styles.viewLogs}
                data-testid="activity-timeline-view-logs"
              >
                View Log
              </span>
            )}
          </div>
        </button>
      );
    },
    [onItemClicked],
  );

  return (
    <List
      className={styles.collapse}
      bordered={false}
      split={false}
      data-testid="activity-timeline-list"
    >
      {items.map(renderItem)}
    </List>
  );
};

export default ActivityTimelineList;
