import { Tabs, TabsProps, Typography } from "antd/lib";
import classNames from "classnames";
import React from "react";

import styles from "./CustomTabs.module.scss";

export interface CustomTabsProps extends Omit<TabsProps, "title"> {
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

      const existingExtra =
        typeof tabBarExtraContent === "object" &&
        tabBarExtraContent !== null &&
        !React.isValidElement(tabBarExtraContent)
          ? (tabBarExtraContent as {
              left?: React.ReactNode;
              right?: React.ReactNode;
            })
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

export const CustomTabs = withCustomProps(Tabs);
