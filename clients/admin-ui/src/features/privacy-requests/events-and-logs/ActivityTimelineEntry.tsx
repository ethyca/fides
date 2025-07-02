import classNames from "classnames";
import { AntTag as Tag, AntTypography as Typography } from "fidesui";
import React from "react";

import { formatDate } from "~/features/common/utils";

import {
  ActivityTimelineItem,
  ActivityTimelineItemTypeEnum,
  TimelineItemColorMap,
} from "../types";
import styles from "./ActivityTimelineEntry.module.scss";

interface ActivityTimelineEntryProps {
  item: ActivityTimelineItem;
}

const ActivityTimelineEntry = ({ item }: ActivityTimelineEntryProps) => {
  const {
    author,
    title,
    date,
    type,
    onClick,
    isError,
    isSkipped,
    isAwaitingInput,
    description,
  } = item;

  // Format the date for display
  const formattedDate = formatDate(date);

  const isClickable = !!onClick;

  const content = (
    <>
      <div className={styles.header}>
        <span className={styles.author} data-testid="activity-timeline-author">
          {author}:
        </span>
        {title && (
          <span
            className={classNames(styles.title, {
              [styles["title--error"]]: isError,
              [styles["title--awaiting-input"]]: isAwaitingInput,
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
          {formattedDate}
        </span>
        <Tag
          className={styles.type}
          color={TimelineItemColorMap[type]}
          data-testid="activity-timeline-type"
        >
          {type}
        </Tag>
        {(isError || isSkipped || isAwaitingInput) && (
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
          <Typography.Paragraph className="!mb-0 whitespace-pre-wrap">
            {description}
          </Typography.Paragraph>
        </div>
      )}
    </>
  );

  const commonProps = {
    className: classNames(styles.itemButton, {
      [styles["itemButton--error"]]: isError,
      [styles["itemButton--awaiting-input"]]: isAwaitingInput,
      [styles["itemButton--clickable"]]: isClickable,
      [styles["itemButton--comment"]]:
        type === ActivityTimelineItemTypeEnum.INTERNAL_COMMENT,
    }),
    "data-testid": "activity-timeline-item",
  };

  // Render a button for clickable items, or a div for non-clickable items
  // This maintains the same styling and data-testid attributes while changing the HTML element
  return isClickable ? (
    <button type="button" onClick={onClick} {...commonProps}>
      {content}
    </button>
  ) : (
    <div {...commonProps}>{content}</div>
  );
};

export default ActivityTimelineEntry;
