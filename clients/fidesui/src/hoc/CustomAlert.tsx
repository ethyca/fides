import { Alert, AlertProps } from "antd/lib";
import type { AlertRef } from "antd/lib/alert/Alert";
import React from "react";

import {
  type FeedbackType,
  getDefaultAlertIcon,
} from "../lib/carbon-icon-defaults";

export interface CustomAlertProps extends AlertProps {}

const withCustomProps = (WrappedComponent: typeof Alert) => {
  const WrappedAlert = React.forwardRef<AlertRef, CustomAlertProps>(
    ({ showIcon, icon, type = "info", description, ...props }, ref) => {
      const carbonIcon =
        showIcon && icon === undefined
          ? getDefaultAlertIcon(type as FeedbackType, !!description)
          : icon;

      return (
        <WrappedComponent
          ref={ref}
          showIcon={showIcon}
          icon={carbonIcon}
          type={type}
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
 * All standard Alert props are supported. Passing a custom `icon` overrides
 * the Carbon default.
 */
export const CustomAlert = Object.assign(withCustomProps(Alert), {
  ErrorBoundary: Alert.ErrorBoundary,
});
