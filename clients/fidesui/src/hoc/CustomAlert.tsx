import { Alert, AlertProps } from "antd/lib";
import type { AlertRef } from "antd/lib/alert/Alert";
import React from "react";

import SparkleIcon from "../icons/Sparkle";
import { getDefaultAlertIcon } from "../lib/carbon-icon-defaults";

const AGENT_STYLE: React.CSSProperties = {
  backgroundColor: "var(--fidesui-limestone)",
  borderColor: "var(--fidesui-limestone)",
};

export type CustomAlertType = NonNullable<AlertProps["type"]> | "agent";

export interface CustomAlertProps extends Omit<AlertProps, "type"> {
  /**
   * Alert variant. Extends Ant's `info | success | warning | error` with
   * `agent` — a limestone-surface, sparkle-iconed variant for content
   * surfaced by automated analysis (classifiers, governance engines, etc.).
   */
  type?: CustomAlertType;
}

const withCustomProps = (WrappedComponent: typeof Alert) => {
  const WrappedAlert = React.forwardRef<AlertRef, CustomAlertProps>(
    (
      {
        showIcon = false,
        icon,
        type = "info",
        banner,
        description,
        title,
        message,
        style,
        ...props
      },
      ref,
    ) => {
      const isAgent = type === "agent";
      // Ant's Alert doesn't know about "agent"; render as the info base and
      // layer on our own surface + icon.
      const effectiveType: NonNullable<AlertProps["type"]> = isAgent
        ? "info"
        : type;

      let effectiveIcon = icon;
      if (showIcon && effectiveIcon === undefined) {
        effectiveIcon = isAgent ? (
          <SparkleIcon size={description ? 24 : 16} />
        ) : (
          getDefaultAlertIcon(effectiveType, !!description)
        );
      }

      const resolvedTitle = title ?? message;

      // When both a title and a non-empty description are present, emphasize
      // the title so the alert reads as "headline + detail". A string
      // description of "" or whitespace is treated as empty.
      const hasDescription =
        typeof description === "string"
          ? description.trim().length > 0
          : Boolean(description);
      const effectiveTitle =
        hasDescription &&
        resolvedTitle !== undefined &&
        resolvedTitle !== null ? (
          <strong>{resolvedTitle}</strong>
        ) : (
          resolvedTitle
        );

      return (
        <WrappedComponent
          ref={ref}
          showIcon={showIcon}
          icon={effectiveIcon}
          type={effectiveType}
          banner={banner}
          description={description}
          title={effectiveTitle}
          style={isAgent ? { ...AGENT_STYLE, ...style } : style}
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
 * Adds an `agent` type for content surfaced by automated analysis: rendered
 * with the `SparkleIcon` and a warm limestone surface. Used for governance
 * insights, classifier findings, and similar AI-driven callouts.
 *
 * When both `message` (title) and `description` are provided, the title is
 * auto-bolded so the alert reads as "headline + detail".
 *
 * All standard Alert props are supported. Passing a custom `icon` overrides
 * the Carbon default.
 */
export const CustomAlert = Object.assign(withCustomProps(Alert), {
  ErrorBoundary: Alert.ErrorBoundary,
});
