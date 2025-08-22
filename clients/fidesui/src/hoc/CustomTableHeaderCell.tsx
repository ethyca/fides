import { OverflowMenuVertical } from "@carbon/icons-react";
import { Button, Dropdown, MenuProps } from "antd/lib";
import React from "react";
import { Resizable, ResizeCallbackData } from "react-resizable";

import styles from "./CustomTableHeaderCell.module.scss";

const ResizeHandle = React.forwardRef<HTMLSpanElement>((props, ref) => {
  return (
    // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions, jsx-a11y/click-events-have-key-events
    <span
      ref={ref}
      role="separator"
      aria-orientation="vertical"
      className={styles.customTableHeaderCell__handle}
      onClick={(e) => {
        e.stopPropagation();
      }}
      {...props}
    />
  );
});

ResizeHandle.displayName = "ResizeHandle";

const MenuHeaderCell = (
  props: React.HTMLAttributes<HTMLTableCellElement> & {
    menu?: MenuProps;
  },
) => {
  const { menu, children, ...rest } = props;
  return (
    <th {...rest}>
      <div className={styles.customTableHeaderCell}>
        <div className={styles.customTableHeaderCell__children}>{children}</div>
        <Dropdown trigger={["click"]} menu={menu} placement="bottomRight">
          <Button
            icon={<OverflowMenuVertical title="Menu" />}
            size="small"
            type="text"
            // Use the filter button class name to match other button styles in the table header
            className={`ant-table-filter-trigger ${styles.customTableHeaderCell__button}`}
            onClick={(e) => {
              e.stopPropagation();
            }}
          />
        </Dropdown>
      </div>
    </th>
  );
};

export const CustomTableHeaderCell = (
  props: React.HTMLAttributes<HTMLTableCellElement> & {
    menu?: MenuProps;
    disableResize?: boolean;
    width?: number;
    onResize?: (
      e: React.SyntheticEvent<Element, Event>,
      data: ResizeCallbackData,
    ) => void;
  },
) => {
  const { menu, disableResize, width, onResize, ...rest } = props;
  const doResize = !!width && !disableResize;

  if (menu && !doResize) {
    return <MenuHeaderCell menu={menu} {...rest} />;
  }

  if (menu && doResize) {
    return (
      <Resizable
        width={width}
        height={0}
        handle={<ResizeHandle />}
        onResize={onResize}
      >
        <MenuHeaderCell menu={menu} {...rest} />
      </Resizable>
    );
  }

  if (!menu && doResize) {
    return (
      <Resizable
        width={width}
        height={0}
        handle={<ResizeHandle />}
        onResize={onResize}
      >
        <th {...rest} />
      </Resizable>
    );
  }

  return <th {...rest} />;
};
