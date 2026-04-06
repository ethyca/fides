import { Button, Dropdown, MenuProps } from "antd/lib";

import { OverflowMenuVertical } from "../icons/carbon";
import styles from "./CustomTableHeaderCell.module.scss";

export const CustomTableHeaderCell = (
  props: React.HTMLAttributes<HTMLTableCellElement> & {
    menu?: MenuProps;
    columnKey?: string;
  },
) => {
  const { menu, columnKey, ...rest } = props;
  if (menu) {
    return (
      <th {...rest}>
        <div className={styles.customTableHeaderCell}>
          <div className={styles.customTableHeaderCell__children}>
            {rest.children}
          </div>
          <Dropdown
            trigger={["click"]}
            menu={menu}
            placement="bottomRight"
            {...(columnKey
              ? {
                  overlayClassName: `${columnKey}-header-menu-list`,
                }
              : {})}
          >
            <Button
              aria-label="Menu"
              icon={<OverflowMenuVertical title="Menu" />}
              size="small"
              type="text"
              // Use the filter button class name to match other button styles in the table header
              className={`ant-table-filter-trigger ${styles.customTableHeaderCell__button}`}
              data-testid={columnKey ? `${columnKey}-header-menu` : undefined}
              onClick={(e) => {
                e.stopPropagation();
              }}
            />
          </Dropdown>
        </div>
      </th>
    );
  }
  return <th {...rest} />;
};
