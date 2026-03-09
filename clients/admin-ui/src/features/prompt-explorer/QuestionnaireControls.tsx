import { Card, Input, Select, Space, Switch, Typography } from "fidesui";

import { ACTION_TYPES } from "./constants";
import type { PromptInfo, TemplateSummary } from "./types";

const { Text } = Typography;
const { TextArea } = Input;

interface Question {
  id: string;
  index: number;
  text: string;
}

interface QuestionnaireControlsProps {
  selectedPrompt: PromptInfo | undefined;
  questionSourceTemplate: string | undefined;
  setQuestionSourceTemplate: (value: string | undefined) => void;
  templates: TemplateSummary[] | undefined;
  questions: Question[];
  currentQuestionIndex: number;
  setCurrentQuestionIndex: (value: number) => void;
  currentQuestion: string;
  userMessage: string;
  setUserMessage: (value: string) => void;
  conversationHistory: string;
  setConversationHistory: (value: string) => void;
  selectedAction: string;
  setSelectedAction: (value: string) => void;
  actionParams: string;
  setActionParams: (value: string) => void;
  isFinalQuestion: boolean;
  setIsFinalQuestion: (value: boolean) => void;
  questionToRephrase: string;
  setQuestionToRephrase: (value: string) => void;
  previousPhrasings: string;
  setPreviousPhrasings: (value: string) => void;
}

/**
 * Controls specific to questionnaire-type prompts in the Prompt Explorer.
 * Renders different inputs based on the selected prompt type.
 */
export const QuestionnaireControls = ({
  selectedPrompt,
  questionSourceTemplate,
  setQuestionSourceTemplate,
  templates,
  questions,
  currentQuestionIndex,
  setCurrentQuestionIndex,
  currentQuestion,
  userMessage,
  setUserMessage,
  conversationHistory,
  setConversationHistory,
  selectedAction,
  setSelectedAction,
  actionParams,
  setActionParams,
  isFinalQuestion,
  setIsFinalQuestion,
  questionToRephrase,
  setQuestionToRephrase,
  previousPhrasings,
  setPreviousPhrasings,
}: QuestionnaireControlsProps) => {
  if (!selectedPrompt || selectedPrompt.category !== "questionnaire") {
    return null;
  }

  const promptType = selectedPrompt.prompt_type;

  return (
    <>
      {/* Question Source - for prompts that need questions */}
      {(promptType === "intent_classification" ||
        promptType === "message_generation" ||
        promptType === "question_rephrase_batch") && (
        <Card title="Question Source" size="small">
          <Text type="secondary" className="mb-2 block">
            Load questions from an assessment template
          </Text>
          <Select
            aria-label="Select template for questions"
            placeholder="Select template for questions"
            allowClear
            className="w-full"
            value={questionSourceTemplate}
            onChange={(value) => {
              setQuestionSourceTemplate(value);
              setCurrentQuestionIndex(0);
            }}
            options={templates?.map((t: TemplateSummary) => ({
              label: `${t.name} (${t.question_count} Qs)`,
              value: t.key,
            }))}
          />
          {questions.length > 0 && (
            <Text type="secondary" className="mt-2 block text-xs">
              Loaded {questions.length} questions
            </Text>
          )}
        </Card>
      )}

      {/* Intent Classification specific controls */}
      {promptType === "intent_classification" && (
        <Card title="Conversation State" size="small">
          <Space direction="vertical" className="w-full">
            <div>
              <Text strong className="mb-1 block">
                Current Question ({currentQuestionIndex + 1} of{" "}
                {questions.length || 5})
              </Text>
              {questions.length > 0 ? (
                <Select
                  aria-label="Current question"
                  className="w-full"
                  value={currentQuestionIndex}
                  onChange={(value) => setCurrentQuestionIndex(value)}
                  options={questions.map((q, i) => ({
                    label: `Q${i + 1}: ${q.text.slice(0, 50)}${q.text.length > 50 ? "..." : ""}`,
                    value: i,
                  }))}
                />
              ) : (
                <Input value={currentQuestion} disabled className="text-xs" />
              )}
            </div>
            <div>
              <Text strong className="mb-1 block">
                User Message
              </Text>
              <TextArea
                value={userMessage}
                onChange={(e) => setUserMessage(e.target.value)}
                rows={2}
                placeholder="The user's response..."
              />
            </div>
            <div>
              <Text strong className="mb-1 block">
                Conversation History (optional)
              </Text>
              <TextArea
                value={conversationHistory}
                onChange={(e) => setConversationHistory(e.target.value)}
                rows={3}
                placeholder="Previous messages in the conversation..."
                className="text-xs"
              />
            </div>
          </Space>
        </Card>
      )}

      {/* Message Generation specific controls */}
      {promptType === "message_generation" && (
        <Card title="Action Context" size="small">
          <Space direction="vertical" className="w-full">
            <div>
              <Text strong className="mb-1 block">
                Action Type
              </Text>
              <Select
                aria-label="Action type"
                className="w-full"
                value={selectedAction}
                onChange={(value) => setSelectedAction(value)}
                options={ACTION_TYPES}
              />
            </div>
            <div>
              <Text strong className="mb-1 block">
                User Message
              </Text>
              <TextArea
                value={userMessage}
                onChange={(e) => setUserMessage(e.target.value)}
                rows={2}
              />
            </div>
            <div>
              <Text strong className="mb-1 block">
                Action Params (JSON, optional)
              </Text>
              <TextArea
                value={actionParams}
                onChange={(e) => setActionParams(e.target.value)}
                rows={2}
                placeholder='e.g., {"answer": "Custom answer"}'
                className="font-mono text-xs"
              />
            </div>
            <div className="flex items-center gap-2">
              <Switch
                checked={isFinalQuestion}
                onChange={(checked) => setIsFinalQuestion(checked)}
                size="small"
              />
              <Text>This is the final question</Text>
            </div>
          </Space>
        </Card>
      )}

      {/* Question Rephrase specific controls */}
      {promptType === "question_rephrase" && (
        <Card title="Rephrase Input" size="small">
          <Space direction="vertical" className="w-full">
            <div>
              <Text strong className="mb-1 block">
                Question to Rephrase
              </Text>
              <TextArea
                value={questionToRephrase}
                onChange={(e) => setQuestionToRephrase(e.target.value)}
                rows={2}
              />
            </div>
            <div>
              <Text strong className="mb-1 block">
                Previous Phrasings (one per line)
              </Text>
              <TextArea
                value={previousPhrasings}
                onChange={(e) => setPreviousPhrasings(e.target.value)}
                rows={3}
                placeholder="Previous versions to avoid..."
                className="text-xs"
              />
            </div>
          </Space>
        </Card>
      )}

      {/* Batch Rephrase - just uses question source */}
      {promptType === "question_rephrase_batch" && questions.length > 0 && (
        <Card title="Questions to Rephrase" size="small">
          <Text type="secondary" className="mb-2 block">
            Will rephrase all {questions.length} questions from the selected
            template
          </Text>
          <div className="max-h-32 overflow-y-auto rounded bg-gray-50 p-2 text-xs">
            {questions.map((q, i) => (
              <div key={q.id} className="mb-1">
                {i + 1}. {q.text}
              </div>
            ))}
          </div>
        </Card>
      )}
    </>
  );
};
