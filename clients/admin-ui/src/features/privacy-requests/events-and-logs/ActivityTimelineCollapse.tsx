import classNames from "classnames";
import {
  AntCollapse as Collapse,
  AntCollapseProps as CollapseProps,
  AntTag as Tag,
} from "fidesui";
import { map } from "lodash";

import { formatDate } from "~/features/common/utils";
import { ExecutionLogStatus } from "~/types/api";

import { PrivacyRequestResults } from "../types";
import styles from "./ActivityTimelineCollapse.module.scss";
import EventLog from "./EventLog";

interface ActivityTimelineProps {
  results?: PrivacyRequestResults;
}

const ActivityTimelineCollapse = ({ results }: ActivityTimelineProps) => {
  const items: CollapseProps["items"] = map(results, (values, key) => {
    const isError = values.some(
      (value) => value.status === ExecutionLogStatus.ERROR,
    );

    return {
      key,
      label: (
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
      ),
      children: <EventLog eventLogs={values} openErrorPanel={() => {}} />,
      className: classNames(styles.item, {
        [styles["item--error"]]: isError,
      }),
      classNames: {
        header: styles.header,
        body: "test2",
      },
    };
  });
  return (
    <Collapse
      items={items}
      expandIcon={() => null}
      className={styles.collapse}
      bordered={false}
      ghost
    />
  );
};

export default ActivityTimelineCollapse;
