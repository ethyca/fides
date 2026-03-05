import type { CarbonIconType } from "@carbon/icons-react";
import {
  CheckmarkFilled,
  InformationFilled,
  Misuse,
  WarningFilled,
} from "@carbon/icons-react";
import { Flex } from "antd/lib";
import { ReactNode } from "react";

const MODAL_ICON_SIZE = 24;
const MESSAGE_ICON_SIZE = 16;
const NOTIFICATION_ICON_SIZE = 24;

/**
 * Wraps a Carbon icon for use inside Ant's modal confirm body.
 * The Flex wrapper with flex="none" prevents the icon from being
 * shrunk by the confirm body's flex layout.
 */
const modalIcon = (Icon: CarbonIconType, color: string): ReactNode => (
  <Flex align="center" flex="none" style={{ marginInlineEnd: 12 }}>
    <Icon size={MODAL_ICON_SIZE} style={{ color }} />
  </Flex>
);

const inlineIcon = (
  Icon: CarbonIconType,
  color: string,
  size: number,
  marginInlineEnd?: number,
): ReactNode => <Icon size={size} style={{ color, marginInlineEnd }} />;

const MODAL_ICON_MAP: Record<string, ReactNode> = {
  info: modalIcon(InformationFilled, "var(--fidesui-minos)"),
  success: modalIcon(CheckmarkFilled, "var(--fidesui-success)"),
  warning: modalIcon(WarningFilled, "var(--fidesui-warning)"),
  error: modalIcon(Misuse, "var(--fidesui-error)"),
  confirm: modalIcon(WarningFilled, "var(--fidesui-warning)"),
};

const MESSAGE_ICON_MAP: Record<string, ReactNode> = {
  info: inlineIcon(
    InformationFilled,
    "var(--fidesui-minos)",
    MESSAGE_ICON_SIZE,
    8,
  ),
  success: inlineIcon(
    CheckmarkFilled,
    "var(--fidesui-success)",
    MESSAGE_ICON_SIZE,
    8,
  ),
  warning: inlineIcon(
    WarningFilled,
    "var(--fidesui-warning)",
    MESSAGE_ICON_SIZE,
    8,
  ),
  error: inlineIcon(Misuse, "var(--fidesui-error)", MESSAGE_ICON_SIZE, 8),
};

const NOTIFICATION_ICON_MAP: Record<string, ReactNode> = {
  info: inlineIcon(
    InformationFilled,
    "var(--fidesui-minos)",
    NOTIFICATION_ICON_SIZE,
  ),
  success: inlineIcon(
    CheckmarkFilled,
    "var(--fidesui-success)",
    NOTIFICATION_ICON_SIZE,
  ),
  warning: inlineIcon(
    WarningFilled,
    "var(--fidesui-warning)",
    NOTIFICATION_ICON_SIZE,
  ),
  error: inlineIcon(Misuse, "var(--fidesui-error)", NOTIFICATION_ICON_SIZE),
};

export const getDefaultModalIcon = (type: string): ReactNode =>
  MODAL_ICON_MAP[type] ?? null;

export const getDefaultMessageIcon = (type: string): ReactNode =>
  MESSAGE_ICON_MAP[type] ?? null;

export const getDefaultNotificationIcon = (type: string): ReactNode =>
  NOTIFICATION_ICON_MAP[type] ?? null;
