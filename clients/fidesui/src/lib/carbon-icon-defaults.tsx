import { Flex } from "antd/lib";
import { ReactNode } from "react";

import type { CarbonIconType } from "../icons/carbon";
import {
  CheckmarkFilled,
  InformationFilled,
  Misuse,
  WarningFilled,
} from "../icons/carbon";

export type FeedbackType = "info" | "success" | "warning" | "error";
export type ModalType = FeedbackType | "confirm";

const ALERT_ICON_SIZE = 16;
const ALERT_ICON_SIZE_WITH_DESC = 24;
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

const MODAL_ICON_MAP: Record<ModalType, ReactNode> = {
  info: modalIcon(InformationFilled, "var(--ant-brand-minos)"),
  success: modalIcon(CheckmarkFilled, "var(--ant-color-success)"),
  warning: modalIcon(WarningFilled, "var(--ant-color-warning)"),
  error: modalIcon(Misuse, "var(--ant-color-error)"),
  confirm: modalIcon(WarningFilled, "var(--ant-color-warning)"),
};

const MESSAGE_ICON_MAP: Record<FeedbackType, ReactNode> = {
  info: inlineIcon(
    InformationFilled,
    "var(--ant-brand-minos)",
    MESSAGE_ICON_SIZE,
    8,
  ),
  success: inlineIcon(
    CheckmarkFilled,
    "var(--ant-color-success)",
    MESSAGE_ICON_SIZE,
    8,
  ),
  warning: inlineIcon(
    WarningFilled,
    "var(--ant-color-warning)",
    MESSAGE_ICON_SIZE,
    8,
  ),
  error: inlineIcon(Misuse, "var(--ant-color-error)", MESSAGE_ICON_SIZE, 8),
};

const NOTIFICATION_ICON_MAP: Record<FeedbackType, ReactNode> = {
  info: inlineIcon(
    InformationFilled,
    "var(--ant-brand-minos)",
    NOTIFICATION_ICON_SIZE,
  ),
  success: inlineIcon(
    CheckmarkFilled,
    "var(--ant-color-success)",
    NOTIFICATION_ICON_SIZE,
  ),
  warning: inlineIcon(
    WarningFilled,
    "var(--ant-color-warning)",
    NOTIFICATION_ICON_SIZE,
  ),
  error: inlineIcon(Misuse, "var(--ant-color-error)", NOTIFICATION_ICON_SIZE),
};

const ALERT_ICON_MAP: Record<FeedbackType, CarbonIconType> = {
  info: InformationFilled,
  success: CheckmarkFilled,
  warning: WarningFilled,
  error: Misuse,
};

export const getDefaultAlertIcon = (
  type: FeedbackType,
  hasDescription: boolean,
): ReactNode => {
  const Icon = ALERT_ICON_MAP[type];
  const size = hasDescription ? ALERT_ICON_SIZE_WITH_DESC : ALERT_ICON_SIZE;
  return <Icon size={size} />;
};

export const getDefaultModalIcon = (type: ModalType): ReactNode =>
  MODAL_ICON_MAP[type];

export const getDefaultMessageIcon = (type: FeedbackType): ReactNode =>
  MESSAGE_ICON_MAP[type];

export const getDefaultNotificationIcon = (type: FeedbackType): ReactNode =>
  NOTIFICATION_ICON_MAP[type];
