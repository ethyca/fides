import { Alert, AlertProps } from "antd/lib";
import type { AlertRef } from "antd/lib/alert/Alert";
import React from "react";

import { getDefaultAlertIcon } from "../lib/carbon-icon-defaults";

export interface CustomAlertProps extends AlertProps {}

const withCustomProps = (WrappedComponent: typeof Alert) => {
  const WrappedAlert = React.forwardRef<AlertRef, CustomAlertProps>(
    (
      { showIcon = false, icon, type = "info", banner, description, ...props },
      ref,
    ) => {
      // Override Ant's banner-specific defaults so all alert types
      // behave consistently.
      const carbonIcon =
        showIcon && icon === undefined
          ? getDefaultAlertIcon(type, !!description)
          : icon;

      return (
        <WrappedComponent
          ref={ref}
          showIcon={showIcon}
          icon={carbonIcon}
          type={type}
          banner={banner}
          description={description}
          {...props}
        />
      );
    },
  );

  WrappedAlert.displayName = "CustomAlert";
  return WrappedAlert;
};

/**
 * Higher-order component that extends Ant Design's Alert to use Carbon icons
 * as the default icons for each feedback type (info, success, warning, error).
 *
 * When `showIcon` is true and no custom `icon` is provided, a Carbon icon is
 * injected based on the alert `type`. Icons are sized at 16px for compact
 * alerts and 24px when a `description` is present.
 *
 * Banner mode (`banner={true}`) uses the same defaults as all other alert
 * types (`showIcon=false`, `type="info"`), overriding Ant's internal defaults.
 *
 * All standard Alert props are supported. Passing a custom `icon` overrides
 * the Carbon default.
 */
export const CustomAlert = Object.assign(withCustomProps(Alert), {
  ErrorBoundary: Alert.ErrorBoundary,
});
