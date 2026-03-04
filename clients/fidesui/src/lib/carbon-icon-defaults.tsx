import type { CarbonIconType } from "@carbon/icons-react";
import {
  CheckmarkFilled,
  InformationFilled,
  Misuse,
  WarningFilled,
} from "@carbon/icons-react";
import { Flex } from "antd/lib";
import { ReactNode } from "react";

const ICON_SIZE = 22;

/**
 * Wraps a Carbon icon for use inside Ant's modal confirm body.
 * The Flex wrapper with flex="none" prevents the icon from being
 * shrunk by the confirm body's flex layout.
 */
const icon = (Icon: CarbonIconType, color: string): ReactNode => (
  <Flex align="center" flex="none" style={{ marginInlineEnd: 12 }}>
    <Icon size={ICON_SIZE} style={{ color }} />
  </Flex>
);

const MODAL_ICON_MAP: Record<string, ReactNode> = {
  info: icon(InformationFilled, "var(--fidesui-info)"),
  success: icon(CheckmarkFilled, "var(--fidesui-success)"),
  warning: icon(WarningFilled, "var(--fidesui-warning)"),
  error: icon(Misuse, "var(--fidesui-error)"),
  confirm: icon(WarningFilled, "var(--fidesui-warning)"),
};

export const getDefaultModalIcon = (type: string): ReactNode =>
  MODAL_ICON_MAP[type] ?? null;
