import classNames from "classnames";
import { AntTag as Tag, List, ListItem } from "fidesui";
import { map } from "lodash";

import { formatDate } from "~/features/common/utils";
import { ExecutionLogStatus } from "~/types/api";

import { ExecutionLog, PrivacyRequestResults } from "../types";
import styles from "./ActivityTimelineCollapse.module.scss";

interface ActivityTimelineProps {
  results?: PrivacyRequestResults;
}

const ActivityTimelineCollapse = ({ results }: ActivityTimelineProps) => {
  const items = map(results, (values, key) => ({
    values,
    key,
  }));

  const renderItem = ({
    values,
    key,
  }: {
    values: ExecutionLog[];
    key: string;
  }) => {
    const isError = values.some(
      (value: { status: ExecutionLogStatus }) =>
        value.status === ExecutionLogStatus.ERROR,
    );

    return (
      <ListItem key={key}>
        <div className={styles.headerInner}>
          <span className={styles.author}>Fides:</span>
          <span
            className={classNames(styles.title, {
              [styles["title--error"]]: isError,
            })}
          >
            {key}
            {isError && " failed"}
          </span>
          <span className={styles.timestamp}>
            {formatDate(values[0].updated_at)}
          </span>
          <Tag color="sandstone">Request update</Tag>
          {isError && <span className={styles.viewLogs}>View Log</span>}
        </div>
      </ListItem>
    );
  };

  return <List className={styles.collapse}>{items.map(renderItem)}</List>;
};

export default ActivityTimelineCollapse;
