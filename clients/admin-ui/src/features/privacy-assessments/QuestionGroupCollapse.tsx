import type { CollapseProps } from "antd";
import { Collapse } from "fidesui";

import styles from "./QuestionGroupCollapse.module.scss";

type Props = Omit<CollapseProps, "className">;

export const QuestionGroupCollapse = (props: Props) => (
  <Collapse className={styles.collapse} {...props} />
);
