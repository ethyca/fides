import classNames from "classnames";
import { Button, CUSTOM_TAG_COLOR, Flex, Icons, Tag, Text } from "fidesui";
import type { HTMLAttributes } from "react";

import styles from "./QuestionnaireStatusBar.module.scss";
import { QuestionnaireSessionStatus } from "./types";

interface QuestionnaireStatusBarProps extends HTMLAttributes<HTMLDivElement> {
  status: QuestionnaireSessionStatus;
  stopReason?: string | null;
  timeSinceSent: string;
  answeredCount: number;
  totalCount: number;
  isSendingReminder: boolean;
  onSendReminder: () => void;
  channel: string;
}

const STATUS_CONFIG = {
  [QuestionnaireSessionStatus.IN_PROGRESS]: {
    icon: <Icons.CheckmarkFilled size={16} />,
    label: "Questionnaire sent",
    iconClass: "checkIcon",
  },
  [QuestionnaireSessionStatus.COMPLETED]: {
    icon: <Icons.CheckmarkFilled size={16} />,
    label: "Questionnaire complete",
    iconClass: "checkIcon",
  },
  [QuestionnaireSessionStatus.STOPPED]: {
    icon: <Icons.WarningFilled size={16} />,
    label: "Questionnaire stopped",
    iconClass: "stoppedIcon",
  },
};

export const QuestionnaireStatusBar = ({
  status,
  stopReason,
  timeSinceSent,
  answeredCount,
  totalCount,
  isSendingReminder,
  onSendReminder,
  channel,
  className,
  ...props
}: QuestionnaireStatusBarProps) => {
  const isAllAnswered = answeredCount === totalCount;
  const isStopped = status === QuestionnaireSessionStatus.STOPPED;
  const config =
    STATUS_CONFIG[status] ||
    STATUS_CONFIG[QuestionnaireSessionStatus.IN_PROGRESS];

  let tagColor = CUSTOM_TAG_COLOR.DEFAULT;
  if (isStopped) {
    tagColor = CUSTOM_TAG_COLOR.WARNING;
  } else if (isAllAnswered) {
    tagColor = CUSTOM_TAG_COLOR.SUCCESS;
  }

  return (
    <div className={classNames(styles.container, className)} {...props}>
      <Flex justify="space-between" align="center">
        <Flex align="center" gap="medium">
          <Flex align="center" gap="small">
            <span className={styles[config.iconClass]}>{config.icon}</span>
            <Text strong size="sm">
              {config.label}
            </Text>
          </Flex>
          <Text type="secondary" size="sm">
            Sent {timeSinceSent} to {channel}
          </Text>
          <Flex align="center" gap="small">
            <Text size="sm">Progress:</Text>
            <Tag color={tagColor}>
              {answeredCount}/{totalCount} answered
              {isStopped ? " (stopped)" : ""}
            </Tag>
          </Flex>
          {isStopped && stopReason && (
            <Text type="secondary" size="sm">
              Reason: {stopReason}
            </Text>
          )}
        </Flex>
        {status === QuestionnaireSessionStatus.IN_PROGRESS && (
          <Button
            size="small"
            onClick={onSendReminder}
            loading={isSendingReminder}
          >
            Send reminder
          </Button>
        )}
      </Flex>
    </div>
  );
};
