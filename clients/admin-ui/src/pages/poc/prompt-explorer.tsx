import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  Flex,
  Input,
  InputNumber,
  Layout,
  Radio,
  Row,
  Select,
  Space,
  Spin,
  Switch,
  Typography,
} from "fidesui";
import type { NextPage } from "next";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useFeatures } from "~/features/common/features";
import PageHeader from "~/features/common/PageHeader";
import {
  DataSectionConfig,
  PromptCategory,
  PromptInfo,
  PromptType,
  TemplateSummary,
  useExecutePromptMutation,
  useGetAssessmentsQuery,
  useGetDataSectionsQuery,
  useGetPromptsQuery,
  useGetTemplateQuestionsQuery,
  useGetTemplatesQuery,
  useRenderPromptMutation,
} from "~/features/prompt-explorer/prompt-explorer.slice";

const { Content } = Layout;
const { Text, Paragraph } = Typography;
const { TextArea } = Input;

const defaultDataSections: DataSectionConfig = {
  organization: true,
  data_categories: true,
  data_uses: true,
  data_subjects: true,
  systems: true,
  datasets: true,
  policies: true,
  privacy_notices: true,
  connections: true,
};

// Intent classification action types
const ACTION_TYPES = [
  { value: "answer", label: "Answer" },
  { value: "skip", label: "Skip" },
  { value: "correct", label: "Correct Previous" },
  { value: "wait", label: "Wait" },
  { value: "clarify_question", label: "Clarify Question" },
  { value: "request_clarification", label: "Request Clarification" },
  { value: "acknowledge", label: "Acknowledge" },
  { value: "restart_all", label: "Restart All" },
  { value: "restart_from", label: "Restart From" },
  { value: "summary", label: "Summary" },
];

const PromptExplorer: NextPage = () => {
  const { plus: hasPlus } = useFeatures();

  // State for prompt selection (single select)
  const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<
    PromptCategory | undefined
  >(undefined);

  // State for data sections (assessment prompts only)
  const [dataSections, setDataSections] =
    useState<DataSectionConfig>(defaultDataSections);

  // State for assessment context
  const [selectedAssessmentId, setSelectedAssessmentId] = useState<
    string | undefined
  >(undefined);
  const [selectedTemplateKey, setSelectedTemplateKey] = useState<
    string | undefined
  >(undefined);

  // State for questionnaire prompt inputs
  const [questionSourceTemplate, setQuestionSourceTemplate] = useState<
    string | undefined
  >(undefined);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState<number>(0);
  const [userMessage, setUserMessage] = useState<string>(
    "We use this data for analytics purposes"
  );
  const [conversationHistory, setConversationHistory] = useState<string>("");
  const [selectedAction, setSelectedAction] = useState<string>("answer");
  const [actionParams, setActionParams] = useState<string>("");
  const [isFinalQuestion, setIsFinalQuestion] = useState<boolean>(false);
  const [questionToRephrase, setQuestionToRephrase] = useState<string>(
    "What is the retention period for this data?"
  );
  const [previousPhrasings, setPreviousPhrasings] = useState<string>(
    "How long do you keep this data?"
  );

  // State for rendered prompt and response
  const [renderedPrompt, setRenderedPrompt] = useState<string>("");
  const [llmResponse, setLlmResponse] = useState<string>("");
  const [modelOverride, setModelOverride] = useState<string>("");

  // API queries
  const {
    data: prompts,
    isLoading: promptsLoading,
    error: promptsError,
  } = useGetPromptsQuery(selectedCategory);

  const { data: dataSectionsList } = useGetDataSectionsQuery();
  const { data: assessments } = useGetAssessmentsQuery();
  const { data: templates } = useGetTemplatesQuery();
  const { data: templateQuestions } = useGetTemplateQuestionsQuery(
    questionSourceTemplate || "",
    { skip: !questionSourceTemplate }
  );

  // Mutations
  const [renderPrompt, { isLoading: renderLoading }] =
    useRenderPromptMutation();
  const [executePrompt, { isLoading: executeLoading }] =
    useExecutePromptMutation();

  // Get selected prompt info
  const selectedPrompt = prompts?.find((p) => p.id === selectedPromptId);

  // Build questions list from template
  const questions = useMemo(() => {
    if (!templateQuestions) return [];
    return templateQuestions.map((q, i) => ({
      index: i,
      text: q.question_text,
      id: q.id,
    }));
  }, [templateQuestions]);

  // Get current question text
  const currentQuestion = useMemo(() => {
    if (questions.length === 0) return "What is the retention period for this data?";
    return questions[currentQuestionIndex]?.text || questions[0]?.text || "";
  }, [questions, currentQuestionIndex]);

  // Build questions summary for intent classification
  const questionsSummary = useMemo(() => {
    if (questions.length === 0) {
      return `1. What is the retention period? (not answered yet)
2. Who has access to the data? (not answered yet)
3. Is the data shared with third parties? (not answered yet)`;
    }
    return questions
      .map((q, i) => {
        const status =
          i < currentQuestionIndex
            ? "answered"
            : i === currentQuestionIndex
              ? "current - not answered yet"
              : "not answered yet";
        return `${i + 1}. ${q.text} (${status})`;
      })
      .join("\n");
  }, [questions, currentQuestionIndex]);

  // Handle data section toggle
  const handleDataSectionToggle = useCallback(
    (section: keyof DataSectionConfig) => {
      setDataSections((prev) => ({
        ...prev,
        [section]: !prev[section],
      }));
    },
    []
  );

  // Build questionnaire variables based on prompt type
  const buildQuestionnaireVariables = useCallback(() => {
    const promptType = selectedPrompt?.prompt_type;

    if (promptType === "intent_classification") {
      const totalQuestions = questions.length || 5;
      const questionNum = currentQuestionIndex + 1;
      const unanswered = totalQuestions - currentQuestionIndex;

      let positionDescription = "a middle question";
      if (questionNum === 1) positionDescription = "the first question";
      else if (questionNum === totalQuestions)
        positionDescription = "the final question";

      return {
        current_question_num: questionNum,
        total_questions: totalQuestions,
        current_question: currentQuestion,
        unanswered_count: unanswered,
        position_description: positionDescription,
        final_question_note:
          questionNum === totalQuestions
            ? "\n**This is the FINAL question.**"
            : "",
        questions_summary: questionsSummary,
        user_message: userMessage,
        conversation_history: conversationHistory || "(No previous messages)",
      };
    }

    if (promptType === "message_generation") {
      return {
        action: selectedAction,
        params: actionParams || `{"answer": "${userMessage}"}`,
        current_question: currentQuestion,
        unanswered_count: (questions.length || 5) - currentQuestionIndex - 1,
        is_final: isFinalQuestion,
        user_message: userMessage,
        conversation_history: conversationHistory || "(No previous messages)",
      };
    }

    if (promptType === "question_rephrase") {
      return {
        question: questionToRephrase || currentQuestion,
        previous_phrasings: previousPhrasings
          ? `- ${previousPhrasings.split("\n").join("\n- ")}`
          : "- (none)",
      };
    }

    if (promptType === "question_rephrase_batch") {
      const questionsFormatted =
        questions.length > 0
          ? questions.map((q, i) => `${i + 1}. ${q.text}`).join("\n")
          : `1. What is the retention period?
2. Who has access to the data?
3. Is the data shared with third parties?
4. What security measures are in place?
5. How is consent obtained?`;
      return {
        questions_formatted: questionsFormatted,
      };
    }

    return {};
  }, [
    selectedPrompt?.prompt_type,
    questions,
    currentQuestionIndex,
    currentQuestion,
    questionsSummary,
    userMessage,
    conversationHistory,
    selectedAction,
    actionParams,
    isFinalQuestion,
    questionToRephrase,
    previousPhrasings,
  ]);

  // Render prompt with data
  const handleRenderPrompt = useCallback(async () => {
    if (!selectedPrompt) return;

    try {
      const questionnaireVariables =
        selectedPrompt.category === "questionnaire"
          ? buildQuestionnaireVariables()
          : {};

      const result = await renderPrompt({
        prompt_type: selectedPrompt.prompt_type,
        data_sections: dataSections,
        assessment_id: selectedAssessmentId,
        template_key: selectedTemplateKey,
        questionnaire_variables: questionnaireVariables,
      }).unwrap();

      setRenderedPrompt(result.rendered_prompt);
    } catch (error) {
      console.error("Failed to render prompt:", error);
    }
  }, [
    selectedPrompt,
    buildQuestionnaireVariables,
    dataSections,
    selectedAssessmentId,
    selectedTemplateKey,
    renderPrompt,
  ]);

  // Execute prompt against LLM
  const handleExecutePrompt = useCallback(async () => {
    if (!renderedPrompt) return;

    try {
      const result = await executePrompt({
        prompt: renderedPrompt,
        model: modelOverride || undefined,
      }).unwrap();

      setLlmResponse(result.response_text);
    } catch (error) {
      console.error("Failed to execute prompt:", error);
    }
  }, [renderedPrompt, modelOverride, executePrompt]);

  // Reset prompt when selection changes
  useEffect(() => {
    setRenderedPrompt("");
    setLlmResponse("");
  }, [selectedPromptId]);

  // Clear assessment selection when switching to questionnaire prompts
  useEffect(() => {
    if (selectedPrompt?.category === "questionnaire") {
      setSelectedAssessmentId(undefined);
      setSelectedTemplateKey(undefined);
    }
  }, [selectedPrompt?.category]);

  if (!hasPlus) {
    return (
      <Layout>
        <Content className="overflow-auto px-10 py-6">
          <Alert
            message="Plus Required"
            description="The Prompt Explorer requires Fides Plus."
            type="warning"
            showIcon
          />
        </Content>
      </Layout>
    );
  }

  // Render questionnaire-specific controls based on prompt type
  const renderQuestionnaireControls = () => {
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
            <Text type="secondary" className="block mb-2">
              Load questions from an assessment template
            </Text>
            <Select
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
              <Text type="secondary" className="block mt-2 text-xs">
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
                <Text strong className="block mb-1">
                  Current Question ({currentQuestionIndex + 1} of{" "}
                  {questions.length || 5})
                </Text>
                {questions.length > 0 ? (
                  <Select
                    className="w-full"
                    value={currentQuestionIndex}
                    onChange={(value) => setCurrentQuestionIndex(value)}
                    options={questions.map((q, i) => ({
                      label: `Q${i + 1}: ${q.text.slice(0, 50)}${q.text.length > 50 ? "..." : ""}`,
                      value: i,
                    }))}
                  />
                ) : (
                  <Input
                    value={currentQuestion}
                    disabled
                    className="text-xs"
                  />
                )}
              </div>
              <div>
                <Text strong className="block mb-1">
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
                <Text strong className="block mb-1">
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
                <Text strong className="block mb-1">
                  Action Type
                </Text>
                <Select
                  className="w-full"
                  value={selectedAction}
                  onChange={(value) => setSelectedAction(value)}
                  options={ACTION_TYPES}
                />
              </div>
              <div>
                <Text strong className="block mb-1">
                  User Message
                </Text>
                <TextArea
                  value={userMessage}
                  onChange={(e) => setUserMessage(e.target.value)}
                  rows={2}
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
                <Text strong className="block mb-1">
                  Question to Rephrase
                </Text>
                <TextArea
                  value={questionToRephrase}
                  onChange={(e) => setQuestionToRephrase(e.target.value)}
                  rows={2}
                />
              </div>
              <div>
                <Text strong className="block mb-1">
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
            <Text type="secondary" className="block mb-2">
              Will rephrase all {questions.length} questions from the selected
              template
            </Text>
            <div className="max-h-32 overflow-y-auto text-xs bg-gray-50 p-2 rounded">
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

  return (
    <Layout className="h-screen">
      <Content className="overflow-auto px-10 py-6">
        <PageHeader heading="Prompt Explorer" />
        <Paragraph type="secondary" className="mb-6">
          Developer tool for exploring and testing LLM prompts used in
          assessments and questionnaires.
        </Paragraph>

        {promptsError && (
          <Alert
            message="Failed to load prompts"
            description="Make sure fidesplus is running in dev mode."
            type="error"
            showIcon
            className="mb-4"
          />
        )}

        <Row gutter={[16, 16]}>
          {/* Left sidebar - Prompt Selection */}
          <Col xs={24} md={6}>
            <Card
              title="Prompt Templates"
              size="small"
              className="h-full"
              extra={
                <Select
                  placeholder="Filter"
                  allowClear
                  size="small"
                  className="w-28"
                  value={selectedCategory}
                  onChange={(value) => setSelectedCategory(value)}
                  options={[
                    { label: "Assessment", value: "assessment" },
                    { label: "Questionnaire", value: "questionnaire" },
                  ]}
                />
              }
            >
              {promptsLoading ? (
                <Flex justify="center" className="py-8">
                  <Spin />
                </Flex>
              ) : (
                <Radio.Group
                  value={selectedPromptId}
                  onChange={(e) => setSelectedPromptId(e.target.value)}
                  className="w-full"
                >
                  <Space direction="vertical" className="w-full">
                    {prompts?.map((prompt: PromptInfo) => (
                      <Card
                        key={prompt.id}
                        size="small"
                        className={`cursor-pointer transition-all ${
                          selectedPromptId === prompt.id
                            ? "border-primary bg-primary/5"
                            : "hover:border-primary/50"
                        }`}
                        onClick={() => setSelectedPromptId(prompt.id)}
                      >
                        <Radio value={prompt.id} className="w-full">
                          <Text strong>{prompt.name}</Text>
                        </Radio>
                        <Text
                          type="secondary"
                          className="block text-xs mt-1 ml-6"
                        >
                          {prompt.description}
                        </Text>
                        <Text code className="text-xs ml-6">
                          {prompt.category}
                        </Text>
                      </Card>
                    ))}
                  </Space>
                </Radio.Group>
              )}
            </Card>
          </Col>

          {/* Middle - Configuration */}
          <Col xs={24} md={6}>
            <Space direction="vertical" className="w-full" size="middle">
              {/* Data Sections - only for assessment prompts */}
              {selectedPrompt?.category === "assessment" && (
                <Card title="Data Sections" size="small">
                  <Text type="secondary" className="block mb-3">
                    Toggle which Fides data to include in the prompt context.
                  </Text>
                  <Space direction="vertical" className="w-full">
                    {dataSectionsList?.map(
                      (section: { id: string; name: string }) => (
                        <Checkbox
                          key={section.id}
                          checked={
                            dataSections[section.id as keyof DataSectionConfig]
                          }
                          onChange={() =>
                            handleDataSectionToggle(
                              section.id as keyof DataSectionConfig
                            )
                          }
                        >
                          {section.name}
                        </Checkbox>
                      )
                    )}
                  </Space>
                </Card>
              )}

              {/* Assessment Context - only for assessment prompts */}
              {selectedPrompt?.category === "assessment" && (
                <Card title="Assessment Context" size="small">
                  <Text type="secondary" className="block mb-3">
                    Select a template for questions, or an existing assessment.
                  </Text>
                  <Space direction="vertical" className="w-full">
                    <div>
                      <Text strong className="block mb-1">
                        Template (for questions)
                      </Text>
                      <Select
                        placeholder="Select template"
                        allowClear
                        className="w-full"
                        value={selectedTemplateKey}
                        onChange={(value) => {
                          setSelectedTemplateKey(value);
                          if (value) setSelectedAssessmentId(undefined);
                        }}
                        options={templates?.map((t: TemplateSummary) => ({
                          label: `${t.name} (${t.question_count} Qs)`,
                          value: t.key,
                        }))}
                      />
                    </div>
                    <Text type="secondary" className="text-center block">
                      — or —
                    </Text>
                    <div>
                      <Text strong className="block mb-1">
                        Existing Assessment
                      </Text>
                      <Select
                        placeholder="Select existing assessment"
                        allowClear
                        className="w-full"
                        value={selectedAssessmentId}
                        onChange={(value) => {
                          setSelectedAssessmentId(value);
                          if (value) setSelectedTemplateKey(undefined);
                        }}
                        options={assessments?.map((a) => ({
                          label: `${a.system_name || a.system_fides_key || "No system"}: ${a.name || `Assessment ${a.id.slice(0, 8)}`} (${a.status})`,
                          value: a.id,
                        }))}
                      />
                    </div>
                  </Space>
                </Card>
              )}

              {/* Questionnaire-specific controls */}
              {renderQuestionnaireControls()}

              {/* Actions */}
              <Card size="small">
                <Space direction="vertical" className="w-full">
                  <Button
                    type="primary"
                    block
                    onClick={handleRenderPrompt}
                    loading={renderLoading}
                    disabled={!selectedPrompt}
                  >
                    Render Prompt
                  </Button>
                  <div>
                    <Text strong className="block mb-1">
                      Model Override
                    </Text>
                    <Input
                      placeholder="e.g., openrouter/google/gemini-2.5-flash"
                      value={modelOverride}
                      onChange={(e) => setModelOverride(e.target.value)}
                      size="small"
                    />
                  </div>
                  <Button
                    type="default"
                    block
                    onClick={handleExecutePrompt}
                    loading={executeLoading}
                    disabled={!renderedPrompt}
                  >
                    Execute Prompt
                  </Button>
                </Space>
              </Card>
            </Space>
          </Col>

          {/* Right - Output */}
          <Col xs={24} md={12}>
            <Space direction="vertical" className="w-full h-full" size="middle">
              {/* Rendered Prompt */}
              <Card
                title="Rendered Prompt"
                size="small"
                className="flex-1"
                extra={
                  renderedPrompt && (
                    <Text type="secondary">
                      {renderedPrompt.length.toLocaleString()} chars
                    </Text>
                  )
                }
              >
                <TextArea
                  value={renderedPrompt}
                  onChange={(e) => setRenderedPrompt(e.target.value)}
                  rows={15}
                  placeholder="Click 'Render Prompt' to generate the prompt with Fides data..."
                  className="font-mono text-xs"
                />
              </Card>

              {/* LLM Response */}
              <Card
                title="LLM Response"
                size="small"
                className="flex-1"
                extra={
                  llmResponse && (
                    <Text type="secondary">
                      {llmResponse.length.toLocaleString()} chars
                    </Text>
                  )
                }
              >
                <TextArea
                  value={llmResponse}
                  readOnly
                  rows={15}
                  placeholder="Click 'Execute Prompt' to send to the LLM..."
                  className="font-mono text-xs"
                />
              </Card>
            </Space>
          </Col>
        </Row>
      </Content>
    </Layout>
  );
};

export default PromptExplorer;
