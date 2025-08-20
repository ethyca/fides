import { OverflowMenuVertical } from "@carbon/icons-react";
import { Button, Dropdown, MenuProps } from "antd/lib";

import styles from "./CustomTableHeaderCell.module.scss";

export const CustomTableHeaderCell = (
  props: React.HTMLAttributes<HTMLTableCellElement> & { menu?: MenuProps },
) => {
  const { menu, children, ...rest } = props;
  if (menu) {
    return (
      <th {...rest}>
        <div className={styles.customTableHeaderCell}>
          <div className={styles.customTableHeaderCell__children}>
            {children}
          </div>
          <Dropdown trigger={["click"]} menu={menu} placement="bottomRight">
            <Button
              icon={<OverflowMenuVertical title="Menu" />}
              size="small"
              type="text"
              // Use the filter button class name to match other button styles in the table header
              className={`ant-table-filter-trigger ${styles.customTableHeaderCell__button}`}
            />
          </Dropdown>
        </div>
      </th>
    );
  }
  return <th {...props} />;
};
