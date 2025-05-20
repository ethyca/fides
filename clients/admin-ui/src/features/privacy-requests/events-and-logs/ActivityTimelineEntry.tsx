import classNames from "classnames";
import { AntTag as Tag, AntTypography as Typography } from "fidesui";
import React from "react";

import { ActivityTimelineItem, TimelineItemColorMap } from "../types";
import styles from "./ActivityTimelineEntry.module.scss";

interface ActivityTimelineEntryProps {
  item: ActivityTimelineItem;
}

const ActivityTimelineEntry = ({ item }: ActivityTimelineEntryProps) => {
  const { author, title, date, tag, onClick, isError, isSkipped, description } =
    item;

  const isClickable = !!onClick;
  const handleClick = onClick || (() => {});

  return (
    <button
      type="button"
      onClick={handleClick}
      className={classNames(styles.itemButton, {
        [styles["itemButton--error"]]: isError,
        [styles["itemButton--clickable"]]: isClickable,
      })}
      data-testid="activity-timeline-item"
    >
      <div className={styles.header}>
        <span className={styles.author} data-testid="activity-timeline-author">
          {author}:
        </span>
        {title && (
          <span
            className={classNames(styles.title, {
              [styles["title--error"]]: isError,
            })}
            data-testid="activity-timeline-title"
          >
            {title}
            {isError && " failed"}
          </span>
        )}
        <span
          className={styles.timestamp}
          data-testid="activity-timeline-timestamp"
        >
          {date}
        </span>
        <Tag
          className={styles.type}
          color={TimelineItemColorMap[tag]}
          data-testid="activity-timeline-type"
        >
          {tag}
        </Tag>
        {(isError || isSkipped) && (
          <span
            className={styles.viewLogs}
            data-testid="activity-timeline-view-logs"
          >
            View Log
          </span>
        )}
      </div>
      {description && (
        <div className="mt-2 pl-2.5">
          <Typography.Paragraph>{description}</Typography.Paragraph>
        </div>
      )}
    </button>
  );
};

export default ActivityTimelineEntry;
