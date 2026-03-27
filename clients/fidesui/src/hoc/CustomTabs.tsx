import { Tabs, TabsProps, Typography } from "antd/lib";
import classNames from "classnames";
import React from "react";

import styles from "./CustomTabs.module.scss";

export interface CustomTabsProps extends Omit<TabsProps, "title"> {
  /**
   * When provided, renders a title inline to the left of the tabs
   * with the tab bar pushed to the right. The title sits inside
   * the tab nav so it shares the bottom border.
   */
  title?: React.ReactNode;
}

const withCustomProps = (WrappedComponent: typeof Tabs) => {
  const WrappedTabs = React.forwardRef<HTMLDivElement, CustomTabsProps>(
    ({ title, className, tabBarExtraContent, ...props }, ref) => {
      if (!title) {
        return (
          <WrappedComponent
            ref={ref as React.Ref<any>}
            className={className}
            tabBarExtraContent={tabBarExtraContent}
            {...props}
          />
        );
      }

      const resolvedTitle =
        typeof title === "string" ? (
          <Typography.Text strong>{title}</Typography.Text>
        ) : (
          title
        );

      // Merge with any existing tabBarExtraContent
      const existingExtra =
        typeof tabBarExtraContent === "object" &&
        tabBarExtraContent !== null &&
        !React.isValidElement(tabBarExtraContent)
          ? (tabBarExtraContent as { left?: React.ReactNode; right?: React.ReactNode })
          : { right: tabBarExtraContent };

      return (
        <WrappedComponent
          ref={ref as React.Ref<any>}
          className={classNames(styles.inlineTitle, className)}
          tabBarExtraContent={{
            left: (
              <>
                {resolvedTitle}
                {existingExtra.left}
              </>
            ),
            right: existingExtra.right,
          }}
          {...props}
        />
      );
    },
  );

  WrappedTabs.displayName = "CustomTabs";
  return WrappedTabs;
};

/**
 * Extends Ant Design's Tabs. When a `title` prop is provided the title is
 * rendered inside the tab bar on the left, sharing the bottom border, with
 * the tab items pushed to the right.
 */
export const CustomTabs = withCustomProps(Tabs);
