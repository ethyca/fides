import { Alert, AlertProps, Button, ConfigProvider, Flex, theme } from "antd/lib";
import type { AlertRef } from "antd/lib/alert/Alert";
import React from "react";

const ALERT_TYPE_TOKEN_MAP = {
  success: "colorSuccess",
  info: "colorInfo",
  warning: "colorWarning",
  error: "colorError",
} as const;

export interface AlertAction {
  label: React.ReactNode;
  onClick: () => void;
}

export interface CustomAlertProps extends AlertProps {
  /** Primary CTA button rendered below the alert content (filled style). */
  primaryAction?: AlertAction;
  /** Secondary CTA button rendered next to the primary action (outlined style). */
  secondaryAction?: AlertAction;
}

const withCustomProps = (WrappedComponent: typeof Alert) => {
  const WrappedAlert = React.forwardRef<AlertRef, CustomAlertProps>(
    (
      {
        primaryAction,
        secondaryAction,
        description,
        className,
        type,
        ...props
      },
      ref,
    ) => {
      const { token } = theme.useToken();
      const hasActions = primaryAction || secondaryAction;

      const colorPrimary =
        token[ALERT_TYPE_TOKEN_MAP[type ?? "info"]];

      const augmentedDescription = hasActions ? (
        <>
          {description}
          <ConfigProvider theme={{ token: { colorPrimary } }}>
            <Flex gap="small" style={{ marginTop: token.marginSM }}>
              {primaryAction && (
                <Button
                  type="primary"
                  size="small"
                  onClick={primaryAction.onClick}
                >
                  {primaryAction.label}
                </Button>
              )}
              {secondaryAction && (
                <Button size="small" onClick={secondaryAction.onClick}>
                  {secondaryAction.label}
                </Button>
              )}
            </Flex>
          </ConfigProvider>
        </>
      ) : (
        description
      );

      return (
        <WrappedComponent
          ref={ref}
          type={type}
          className={className}
          description={augmentedDescription}
          {...props}
        />
      );
    },
  );

  WrappedAlert.displayName = "CustomAlert";
  return WrappedAlert;
};

/**
 * Higher-order component that extends Ant Design's Alert with support for
 * primary and secondary call-to-action buttons rendered below the alert content.
 *
 * @param {AlertAction} [primaryAction] - Primary CTA button (filled style).
 * @param {AlertAction} [secondaryAction] - Secondary CTA button (outlined style).
 *
 * @example
 * <Alert
 *   type="warning"
 *   message="Action required"
 *   description="There are 3 unresolved items that need your attention."
 *   showIcon
 *   primaryAction={{ label: "View actions →", onClick: () => navigate("/actions") }}
 *   secondaryAction={{ label: "Dismiss", onClick: () => setDismissed(true) }}
 * />
 */
export const CustomAlert = Object.assign(withCustomProps(Alert), {
  ErrorBoundary: Alert.ErrorBoundary,
});
