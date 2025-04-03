import {
  AntCollapse as Collapse,
  AntCollapseProps as CollapseProps,
  AntTag as Tag,
} from "fidesui";
import { map } from "lodash";

import { formatDate } from "~/features/common/utils";

import { ExecutionLog } from "../types";
import styles from "./ActivityTimelineCollapse.module.scss";
import EventLog from "./EventLog";

interface ActivityTimelineProps {
  results: Record<string, ExecutionLog[]>;
}

const ActivityTimelineCollapse = ({ results }: ActivityTimelineProps) => {
  const items: CollapseProps["items"] = map(results, (values, key) => ({
    key,
    label: (
      <div className={styles.headerInner}>
        <span className={styles.author}>Fides:</span>
        <span className={styles.title}>{key}</span>
        <span className={styles.timestamp}>
          {formatDate(values[0].updated_at)}
        </span>
        <Tag color="sandstone">Request update</Tag>
      </div>
    ),
    children: <EventLog eventLogs={values} openErrorPanel={() => {}} />,
    className: styles.item,
    classNames: {
      header: styles.header,
      body: "test2",
    },
  }));
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
