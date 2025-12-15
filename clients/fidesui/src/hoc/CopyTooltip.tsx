import { Button, Tooltip, TooltipProps } from "antd/lib";
import React, { ReactNode, useState } from "react";

import styles from "./CopyTooltip.module.scss";

interface CopyTooltipProps extends Omit<TooltipProps, "title"> {
  children: ReactNode;
  /** The content to copy to clipboard when the tooltip is clicked */
  contentToCopy: string;
  /** Custom text to show before copying (defaults to "Copy ID") */
  copyText?: string;
  /** Custom text to show after copying (defaults to "Copied!") */
  copiedText?: string;
  /** Duration in milliseconds to show "Copied!" message before reverting (defaults to 2000) */
  copiedDuration?: number;
}

/**
 * CopyTooltip is a wrapper component that displays a clickable tooltip with copy-to-clipboard functionality.
 * The tooltip text itself is clickable - when clicked, it copies the provided content to the clipboard
 * and shows a confirmation message.
 *
 * Features:
 * - Shows "Copy ID" (or custom text) tooltip on hover
 * - Click the tooltip text to copy content to clipboard
 * - Shows "Copied!" (or custom text) confirmation
 * - Automatically reverts to original text after configured duration
 *
 * @example
 * ```tsx
 * // Basic usage with default text
 * <CopyTooltip contentToCopy="123e4567-e89b-12d3-a456-426614174000">
 *   <span>System ID: 123e4567</span>
 * </CopyTooltip>
 *
 * // With custom text
 * <CopyTooltip
 *   contentToCopy="user@example.com"
 *   copyText="Copy email"
 *   copiedText="Email copied!"
 * >
 *   <span>user@example.com</span>
 * </CopyTooltip>
 * ```
 */
export const CopyTooltip = ({
  children,
  contentToCopy,
  copyText = "Copy ID",
  copiedText = "Copied!",
  copiedDuration = 2000,
  ...props
}: CopyTooltipProps) => {
  const [hasCopied, setHasCopied] = useState<boolean>(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(contentToCopy);
      setHasCopied(true);

      setTimeout(() => {
        setHasCopied(false);
      }, copiedDuration);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error("Failed to copy to clipboard:", err);
    }
  };

  const handleClick = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await handleCopy();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      e.stopPropagation();
      handleCopy();
    }
  };

  const tooltipContent = (
    <Button
      type="text"
      size="small"
      onClick={handleClick}
      disabled={hasCopied}
      className={styles.tooltipButton}
    >
      {hasCopied
        ? copiedText
        : `Press enter or space to ${copyText.toLowerCase()}`}
    </Button>
  );

  return (
    <Tooltip
      mouseEnterDelay={0.3}
      mouseLeaveDelay={0.3}
      {...props}
      title={tooltipContent}
      trigger={["focus", "hover"]}
      rootClassName={styles.tooltip}
    >
      <span
        role="button"
        tabIndex={0}
        onKeyDown={handleKeyDown}
        style={{ cursor: "default" }}
      >
        {children}
      </span>
    </Tooltip>
  );
};
