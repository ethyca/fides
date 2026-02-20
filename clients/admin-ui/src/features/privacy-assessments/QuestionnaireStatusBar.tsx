import classNames from "classnames";
import { Button, CUSTOM_TAG_COLOR, Flex, Icons, Tag, Text } from "fidesui";
import type { HTMLAttributes } from "react";

import styles from "./QuestionnaireStatusBar.module.scss";
import { SlackIcon } from "./SlackIcon";

interface QuestionnaireStatusBarProps extends HTMLAttributes<HTMLDivElement> {
  timeSinceSent: string;
  answeredCount: number;
  totalCount: number;
  isSendingReminder: boolean;
  onSendReminder: () => void;
}

export const QuestionnaireStatusBar = ({
  timeSinceSent,
  answeredCount,
  totalCount,
  isSendingReminder,
  onSendReminder,
  className,
  ...props
}: QuestionnaireStatusBarProps) => {
  const isAllAnswered = answeredCount === totalCount;

  return (
    <div className={classNames(styles.container, className)} {...props}>
      <Flex justify="space-between" align="center">
        <Flex align="center" gap="middle">
          <Flex align="center" gap="small">
            <Icons.CheckmarkFilled size={16} className={styles.checkIcon} />
            <Text strong size="sm">
              Questionnaire sent
            </Text>
          </Flex>
          <Text type="secondary" size="sm">
            Sent {timeSinceSent} to #privacy-team
          </Text>
          <Flex align="center" gap="small">
            <Text size="sm">Progress:</Text>
            <Tag
              color={
                isAllAnswered
                  ? CUSTOM_TAG_COLOR.SUCCESS
                  : CUSTOM_TAG_COLOR.DEFAULT
              }
            >
              {answeredCount}/{totalCount} answered
            </Tag>
          </Flex>
        </Flex>
        <Button
          icon={<SlackIcon size={14} />}
          size="small"
          onClick={onSendReminder}
          loading={isSendingReminder}
        >
          Send reminder
        </Button>
      </Flex>
    </div>
  );
};
