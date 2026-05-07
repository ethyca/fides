import classNames from "classnames";
import { Icons, Tag, Tooltip, Typography } from "fidesui";
import React from "react";

import { formatDate, pluralize } from "~/features/common/utils";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";

import {
  ActivityTimelineItem,
  ActivityTimelineItemTypeEnum,
  TimelineItemColorMap,
} from "../types";
import styles from "./ActivityTimelineEntry.module.scss";
import { AttachmentDisplay } from "./AttachmentDisplay";

const TIMELINE_ICON_SIZE = 20;

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
    isPolling,
    description,
    attachments,
    logCount = 0,
    connectionLogo,
    icon,
  } = item;

  // Format the date for display
  const formattedDate = formatDate(date);
  const showViewLog = logCount > 0;

  const isClickable = !!onClick;

  const hasAttachments = attachments && attachments.length > 0;

  // The "Fides" author label is implied by the system icon, so we only
  // surface a name for entries authored by an actual user (comments, manual
  // task completions, etc.).
  const showAuthorName = author && author !== "Fides";

  const leadingIcon = connectionLogo ? (
    <ConnectionTypeLogo data={connectionLogo} size={TIMELINE_ICON_SIZE} />
  ) : (
    icon
  );

  const content = (
    <>
      <div className={styles.header}>
        {leadingIcon && (
          <span className={styles.icon} data-testid="activity-timeline-icon">
            {leadingIcon}
          </span>
        )}
        {showAuthorName && (
          <span
            className={styles.author}
            data-testid="activity-timeline-author"
          >
            {author}:
          </span>
        )}
        {title && (
          <Typography.Text
            className={classNames(styles.title, {
              [styles["title--error"]]: isError,
              [styles["title--awaiting-input"]]: isAwaitingInput,
              [styles["title--polling"]]: isPolling,
            })}
            ellipsis={{ tooltip: true }}
            data-testid="activity-timeline-title"
          >
            {title}

            {isError && " failed"}
          </Typography.Text>
        )}
        <div className="hidden xl:block">
          <Typography.Text
            className={styles.timestamp}
            data-testid="activity-timeline-timestamp"
          >
            {formattedDate}
          </Typography.Text>
        </div>
        <div className="xl:hidden">
          <Tooltip title={formattedDate}>
            <Icons.Time data-testid="activity-timeline-timestamp-icon" />
          </Tooltip>
        </div>
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
            · View {logCount} {pluralize(logCount, "Log", "Logs")}
          </span>
        )}
      </div>
      {(description || hasAttachments) && (
        <div className="mt-2 flex justify-between pl-2.5 align-top">
          <Typography.Paragraph
            className="!mb-0 whitespace-pre-wrap"
            data-testid="activity-timeline-description"
          >
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
      [styles["itemButton--polling"]]: isPolling,
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
