import { Alert, AlertProps } from "antd/lib";
import type { AlertRef } from "antd/lib/alert/Alert";
import React from "react";

import { getDefaultAlertIcon } from "../lib/carbon-icon-defaults";

export interface CustomAlertProps extends AlertProps {}

const withCustomProps = (WrappedComponent: typeof Alert) => {
  const WrappedAlert = React.forwardRef<AlertRef, CustomAlertProps>(
    ({ showIcon, icon, type, banner, description, ...props }, ref) => {
      // Mirror Ant's internal defaults so Carbon icons apply correctly:
      // - banner mode defaults type to "warning" (not "info")
      // - banner mode implicitly enables showIcon
      const resolvedType = type ?? (banner ? "warning" : "info");
      const resolvedShowIcon = showIcon ?? !!banner;

      const carbonIcon =
        resolvedShowIcon && icon === undefined
          ? getDefaultAlertIcon(resolvedType, !!description)
          : icon;

      return (
        <WrappedComponent
          ref={ref}
          showIcon={resolvedShowIcon}
          icon={carbonIcon}
          type={resolvedType}
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
 * Banner mode (`banner={true}`) mirrors Ant's internal defaults: `showIcon`
 * defaults to true and `type` defaults to "warning" when not explicitly set.
 *
 * All standard Alert props are supported. Passing a custom `icon` overrides
 * the Carbon default.
 */
export const CustomAlert = Object.assign(withCustomProps(Alert), {
  ErrorBoundary: Alert.ErrorBoundary,
});
