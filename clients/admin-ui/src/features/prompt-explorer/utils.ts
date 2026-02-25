import type { PromptType } from "./types";

interface Question {
  id: string;
  index: number;
  text: string;
}

interface IntentClassificationParams {
  questions: Question[];
  currentQuestionIndex: number;
  currentQuestion: string;
  questionsSummary: string;
  userMessage: string;
  conversationHistory: string;
}

interface MessageGenerationParams {
  questions: Question[];
  currentQuestionIndex: number;
  currentQuestion: string;
  selectedAction: string;
  actionParams: string;
  userMessage: string;
  conversationHistory: string;
  isFinalQuestion: boolean;
}

interface QuestionRephraseParams {
  questionToRephrase: string;
  currentQuestion: string;
  previousPhrasings: string;
}

interface QuestionRephraseBatchParams {
  questions: Question[];
}

export type QuestionnaireVariablesParams = {
  promptType: PromptType | undefined;
} & Partial<IntentClassificationParams> &
  Partial<MessageGenerationParams> &
  Partial<QuestionRephraseParams> &
  Partial<QuestionRephraseBatchParams>;

/**
 * Build questionnaire variables based on prompt type.
 * These variables are used to populate the prompt template before rendering.
 */
export const buildQuestionnaireVariables = ({
  promptType,
  questions = [],
  currentQuestionIndex = 0,
  currentQuestion = "",
  questionsSummary = "",
  userMessage = "",
  conversationHistory = "",
  selectedAction = "",
  actionParams = "",
  isFinalQuestion = false,
  questionToRephrase = "",
  previousPhrasings = "",
}: QuestionnaireVariablesParams): Record<string, unknown> => {
  if (promptType === "intent_classification") {
    const totalQuestions = questions.length || 5;
    const questionNum = currentQuestionIndex + 1;
    const unanswered = totalQuestions - currentQuestionIndex;

    let positionDescription = "a middle question";
    if (questionNum === 1) {
      positionDescription = "the first question";
    } else if (questionNum === totalQuestions) {
      positionDescription = "the final question";
    }

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
};
