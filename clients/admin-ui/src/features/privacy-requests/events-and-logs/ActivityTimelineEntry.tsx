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
import { AttachmentDisplay } from "./AttachmentDisplay";

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
    isAwaitingInput,
    description,
    attachments,
    showViewLog,
  } = item;

  // Format the date for display
  const formattedDate = formatDate(date);

  const isClickable = !!onClick;

  const hasAttachments = attachments && attachments.length > 0;

  const content = (
    <>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span
            className={styles.author}
            data-testid="activity-timeline-author"
          >
            {author}:
          </span>
          {title && (
            <Typography.Text
              className={classNames(styles.title, {
                [styles["title--error"]]: isError,
                [styles["title--awaiting-input"]]: isAwaitingInput,
              })}
              ellipsis={{ tooltip: true }}
              style={{ maxWidth: "33%" }}
              data-testid="activity-timeline-title"
            >
              {title}
              {isError && " failed"}
            </Typography.Text>
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
          {showViewLog && (
            <span
              className={styles.viewLogs}
              data-testid="activity-timeline-view-logs"
            >
              View Log
            </span>
          )}
        </div>
      </div>
      {(description || hasAttachments) && (
        <div className="mt-2 flex justify-between pl-2.5 align-top">
          <Typography.Paragraph className="!mb-0 whitespace-pre-wrap">
            {description || ""}
          </Typography.Paragraph>
          {hasAttachments && <AttachmentDisplay attachments={attachments} />}
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
      [styles["itemButton--manual-task"]]:
        type === ActivityTimelineItemTypeEnum.MANUAL_TASK,
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
