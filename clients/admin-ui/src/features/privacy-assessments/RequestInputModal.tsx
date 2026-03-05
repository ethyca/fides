import classNames from "classnames";
import {
  Button,
  Checkbox,
  Divider,
  Flex,
  Modal,
  Space,
  Text,
  useMessage,
} from "fidesui";
import { useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { RTKErrorResult } from "~/types/errors/api";

import { AnswerStatusTags } from "./AnswerStatusTags";
import { useCreateQuestionnaireMutation } from "./privacy-assessments.slice";
import styles from "./RequestInputModal.module.scss";
import { AnswerStatus, AssessmentQuestion } from "./types";

interface RequestInputModalProps {
  open: boolean;
  onClose: () => void;
  assessmentId: string;
  questions: AssessmentQuestion[];
  slackChannelName: string;
}

const needsInput = (q: AssessmentQuestion) =>
  q.answer_status === AnswerStatus.NEEDS_INPUT;

export const RequestInputModal = ({
  open,
  onClose,
  assessmentId,
  questions,
  slackChannelName,
}: RequestInputModalProps) => {
  const message = useMessage();
  const [createQuestionnaire, { isLoading }] = useCreateQuestionnaireMutation();

  const defaultSelectedIds = useMemo(
    () => questions.filter((q) => needsInput(q)).map((q) => q.question_id),
    [questions],
  );

  const [selectedIds, setSelectedIds] = useState<string[]>(defaultSelectedIds);

  const handleAfterOpen = (isOpen: boolean) => {
    if (isOpen) {
      setSelectedIds(defaultSelectedIds);
    }
  };

  const handleSelectAll = () =>
    setSelectedIds(questions.map((q) => q.question_id));

  const handleUnselectAll = () => setSelectedIds([]);

  const handleSubmit = async () => {
    try {
      await createQuestionnaire({
        id: assessmentId,
        body: {
          channel: slackChannelName,
          include_question_ids: selectedIds,
        },
      }).unwrap();
      message.success(`Questions sent to ${slackChannelName} on Slack.`);
      onClose();
    } catch (error) {
      message.error(
        getErrorMessage(
          error as RTKErrorResult["error"],
          "Failed to send questionnaire. Please try again.",
        ),
      );
    }
  };

  return (
    <Modal
      title="Request input from team"
      open={open}
      onCancel={onClose}
      afterOpenChange={handleAfterOpen}
      width={600}
      destroyOnClose
      okText="Send questions"
      okButtonProps={{
        disabled: selectedIds.length === 0,
        loading: isLoading,
      }}
      onOk={handleSubmit}
    >
      <Text type="secondary" className="mb-4 block">
        An AI agent will ask the selected questions in{" "}
        <Text strong>{slackChannelName}</Text> on Slack and collect answers from
        your team.
      </Text>

      <Divider className="my-3" />

      <Flex justify="space-between" align="center" className="mb-3">
        <Flex gap="small" align="center">
          <Button type="link" size="small" onClick={handleSelectAll}>
            Select all
          </Button>
          <Text type="secondary">·</Text>
          <Button type="link" size="small" onClick={handleUnselectAll}>
            Unselect all
          </Button>
        </Flex>
        <Text type="secondary" size="sm">
          {selectedIds.length} of {questions.length} selected
        </Text>
      </Flex>

      <Checkbox.Group
        value={selectedIds}
        onChange={(values) => setSelectedIds(values as string[])}
        className="w-full"
      >
        <Space
          direction="vertical"
          size="small"
          className={classNames("w-full", styles.questionList)}
        >
          {questions.map((question) => (
            <div key={question.question_id} className={styles.questionRow}>
              <Flex align="flex-start" gap="small">
                <Checkbox value={question.question_id} className="mt-0.5" />
                <div className="min-w-0 flex-1">
                  <Space direction="vertical" size={4} className="w-full">
                    <Text>
                      {question.id}. {question.question_text}
                    </Text>
                    <Space size="small">
                      <AnswerStatusTags question={question} />
                    </Space>
                  </Space>
                </div>
              </Flex>
            </div>
          ))}
        </Space>
      </Checkbox.Group>
    </Modal>
  );
};
