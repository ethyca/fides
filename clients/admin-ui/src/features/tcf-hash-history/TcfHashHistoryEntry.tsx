import classNames from "classnames";
import { Icons, Tag, Tooltip, Typography } from "fidesui";

import { formatDate } from "~/features/common/utils";
import { TCFVersionHashHistoryResponse } from "~/features/privacy-experience/privacy-experience.slice";
import baseStyles from "~/features/privacy-requests/events-and-logs/ActivityTimelineEntry.module.scss";

import { TRIGGER_SOURCE_COLORS, TRIGGER_SOURCE_LABELS } from "./constants";
import TcfHashDisplay from "./TcfHashDisplay";
import styles from "./TcfHashHistoryEntry.module.scss";

interface Props {
  entry: TCFVersionHashHistoryResponse;
}

const TcfHashHistoryEntry = ({ entry }: Props) => {
  const formattedDate = formatDate(new Date(entry.changed_at));
  const triggerLabel =
    TRIGGER_SOURCE_LABELS[entry.trigger_source] ?? entry.trigger_source;
  const tagColor = TRIGGER_SOURCE_COLORS[entry.trigger_source];

  return (
    <div className={baseStyles.itemButton} data-testid="tcf-hash-history-item">
      <div className={baseStyles.header}>
        <span className={baseStyles.author}>TCF:</span>

        <span
          className={classNames(baseStyles.title, "flex items-center gap-1")}
        >
          <TcfHashDisplay value={entry.previous_hash} />
          <span className={styles.arrow}>→</span>
          <TcfHashDisplay value={entry.current_hash} />
        </span>

        <div className="hidden xl:block">
          <Typography.Text className={baseStyles.timestamp}>
            {formattedDate}
          </Typography.Text>
        </div>
        <div className="xl:hidden">
          <Tooltip title={formattedDate}>
            <Icons.Time />
          </Tooltip>
        </div>

        <Tag className={styles.triggerTag} color={tagColor}>
          {triggerLabel}
        </Tag>
      </div>
    </div>
  );
};

export default TcfHashHistoryEntry;
