/* eslint-disable import/no-extraneous-dependencies */
/**
 * Privacy Assessments MSW Handlers
 *
 * Mock Service Worker handlers for privacy assessment endpoints.
 * These handlers provide mock API responses for development and testing.
 */

import { rest } from "msw";

import {
  AssessmentEvidenceResponse,
  AssessmentQuestion,
  BulkUpdateAnswersResponse,
  CreatePrivacyAssessmentRequest,
  CreatePrivacyAssessmentResponse,
  CreateQuestionnaireRequest,
  CreateReminderRequest,
  Page_PrivacyAssessmentResponse_,
  PrivacyAssessmentDetailResponse,
  PrivacyAssessmentResponse,
  QuestionnaireResponse,
  QuestionnaireStatusResponse,
  ReminderResponse,
  UpdateAnswerRequest,
  UpdateAnswerResponse,
  UpdatePrivacyAssessmentRequest,
} from "~/features/privacy-assessments/types";

import {
  calculateCompleteness,
  determineStatus,
  getEvidenceForGroup,
  mockAssessmentMetadata,
  mockPrivacyAssessment,
  MOCK_ASSESSMENTS,
  MOCK_CPRA_QUESTION_GROUPS,
  MOCK_EVIDENCE_ITEMS,
  MOCK_QUESTIONNAIRE_QUESTIONS,
} from "./data";

/**
 * Privacy assessment MSW handlers
 */
export const privacyAssessmentHandlers = () => {
  const apiBase = "/api/v1";

  // In-memory store for mock state
  let mockAssessments = [...MOCK_ASSESSMENTS];
  let mockQuestionGroups = JSON.parse(JSON.stringify(MOCK_CPRA_QUESTION_GROUPS));
  let mockQuestionnaires: Record<string, QuestionnaireStatusResponse> = {};

  return [
    // =========================================================================
    // GET /plus/privacy-assessments - List all assessments
    // =========================================================================
    rest.get(`${apiBase}/plus/privacy-assessments`, (req, res, ctx) => {
      const page = parseInt(req.url.searchParams.get("page") || "1", 10);
      const size = parseInt(req.url.searchParams.get("size") || "25", 10);
      const statusFilter = req.url.searchParams.get("status");

      // Apply status filter if provided
      let filteredAssessments = [...mockAssessments];
      if (statusFilter) {
        filteredAssessments = filteredAssessments.filter(
          (a) => a.status === statusFilter
        );
      }

      // Apply pagination
      const startIndex = (page - 1) * size;
      const endIndex = startIndex + size;
      const paginatedItems = filteredAssessments.slice(startIndex, endIndex);
      const totalPages = Math.ceil(filteredAssessments.length / size);

      const response: Page_PrivacyAssessmentResponse_ = {
        items: paginatedItems,
        total: filteredAssessments.length,
        page,
        size,
        pages: totalPages,
      };

      return res(ctx.status(200), ctx.json(response));
    }),

    // =========================================================================
    // GET /plus/privacy-assessments/:id - Get single assessment with details
    // =========================================================================
    rest.get(`${apiBase}/plus/privacy-assessments/:id`, (req, res, ctx) => {
      const { id } = req.params;
      const assessment = mockAssessments.find((a) => a.id === id);

      if (!assessment) {
        return res(
          ctx.status(404),
          ctx.json({ detail: "Assessment not found" })
        );
      }

      // Add evidence to question groups
      const questionGroupsWithEvidence = mockQuestionGroups.map(
        (group: typeof MOCK_CPRA_QUESTION_GROUPS[0]) => ({
          ...group,
          questions: group.questions.map((q: AssessmentQuestion) => ({
            ...q,
            evidence: getEvidenceForGroup(group.id, MOCK_EVIDENCE_ITEMS),
          })),
        })
      );

      // Get questionnaire status if exists
      const questionnaire = mockQuestionnaires[id as string] || null;

      const response: PrivacyAssessmentDetailResponse = {
        ...assessment,
        assessment_type: "cpra",
        question_groups: questionGroupsWithEvidence,
        questionnaire: questionnaire
          ? {
              sent_at: questionnaire.sent_at,
              channel: questionnaire.channel,
              total_questions: questionnaire.total_questions,
              answered_questions: questionnaire.answered_questions,
              last_reminder_at: questionnaire.last_reminder_at,
              reminder_count: questionnaire.reminder_count,
            }
          : null,
        metadata: mockAssessmentMetadata(),
      };

      return res(ctx.status(200), ctx.json(response));
    }),

    // =========================================================================
    // POST /plus/privacy-assessments - Create new assessments
    // =========================================================================
    rest.post(
      `${apiBase}/plus/privacy-assessments`,
      async (req, res, ctx) => {
        const body = (await req.json()) as CreatePrivacyAssessmentRequest;

        // Create new assessments based on request
        const newAssessments: PrivacyAssessmentResponse[] = [];

        // For now, create a sample assessment
        const newAssessment = mockPrivacyAssessment({
          id: `assessment-${Date.now()}`,
          name: "New Privacy Assessment",
          status: "in_progress",
          completeness: 0,
        });

        newAssessments.push(newAssessment);
        mockAssessments = [...mockAssessments, ...newAssessments];

        const response: CreatePrivacyAssessmentResponse = {
          assessments: newAssessments,
          assessment_type: body.assessment_type || "cpra",
          assessment_name: "CPRA Risk Assessment",
          total_created: newAssessments.length,
        };

        return res(ctx.status(201), ctx.json(response));
      }
    ),

    // =========================================================================
    // PUT /plus/privacy-assessments/:id - Update assessment metadata
    // =========================================================================
    rest.put(
      `${apiBase}/plus/privacy-assessments/:id`,
      async (req, res, ctx) => {
        const { id } = req.params;
        const body = (await req.json()) as UpdatePrivacyAssessmentRequest;

        const assessmentIndex = mockAssessments.findIndex((a) => a.id === id);
        if (assessmentIndex === -1) {
          return res(
            ctx.status(404),
            ctx.json({ detail: "Assessment not found" })
          );
        }

        // Update the assessment
        mockAssessments[assessmentIndex] = {
          ...mockAssessments[assessmentIndex],
          ...body,
          updated_at: new Date().toISOString(),
          status_updated_at: body.status
            ? new Date().toISOString()
            : mockAssessments[assessmentIndex].status_updated_at,
        };

        return res(ctx.status(200), ctx.json(mockAssessments[assessmentIndex]));
      }
    ),

    // =========================================================================
    // DELETE /plus/privacy-assessments/:id - Delete assessment
    // =========================================================================
    rest.delete(`${apiBase}/plus/privacy-assessments/:id`, (req, res, ctx) => {
      const { id } = req.params;

      const assessmentIndex = mockAssessments.findIndex((a) => a.id === id);
      if (assessmentIndex === -1) {
        return res(
          ctx.status(404),
          ctx.json({ detail: "Assessment not found" })
        );
      }

      // Remove the assessment
      mockAssessments = mockAssessments.filter((a) => a.id !== id);

      // Remove associated questionnaire
      delete mockQuestionnaires[id as string];

      return res(ctx.status(204));
    }),

    // =========================================================================
    // PUT /plus/privacy-assessments/:id/answers/:questionId - Update single answer
    // =========================================================================
    rest.put(
      `${apiBase}/plus/privacy-assessments/:id/answers/:questionId`,
      async (req, res, ctx) => {
        const { id, questionId } = req.params;
        const body = (await req.json()) as UpdateAnswerRequest;

        const assessment = mockAssessments.find((a) => a.id === id);
        if (!assessment) {
          return res(
            ctx.status(404),
            ctx.json({ detail: "Assessment not found" })
          );
        }

        // Find and update the question
        let updatedQuestion: AssessmentQuestion | null = null;

        mockQuestionGroups = mockQuestionGroups.map(
          (group: typeof MOCK_CPRA_QUESTION_GROUPS[0]) => ({
            ...group,
            questions: group.questions.map((q: AssessmentQuestion) => {
              if (q.question_id === questionId || q.id === questionId) {
                updatedQuestion = {
                  ...q,
                  answer_text: body.answer_text,
                  answer_status: body.answer_text.trim() ? "complete" : "needs_input",
                  answer_source: "user_input",
                };
                return updatedQuestion;
              }
              return q;
            }),
          })
        );

        if (!updatedQuestion) {
          return res(
            ctx.status(404),
            ctx.json({ detail: "Question not found" })
          );
        }

        // Recalculate completeness
        const completeness = calculateCompleteness(mockQuestionGroups);
        const status = determineStatus(completeness);

        // Update assessment
        const assessmentIndex = mockAssessments.findIndex((a) => a.id === id);
        mockAssessments[assessmentIndex] = {
          ...mockAssessments[assessmentIndex],
          completeness,
          status,
          updated_at: new Date().toISOString(),
        };

        const response: UpdateAnswerResponse = {
          question: updatedQuestion,
          completeness,
          status,
        };

        return res(ctx.status(200), ctx.json(response));
      }
    ),

    // =========================================================================
    // PUT /plus/privacy-assessments/:id/answers - Bulk update answers
    // =========================================================================
    rest.put(
      `${apiBase}/plus/privacy-assessments/:id/answers`,
      async (req, res, ctx) => {
        const { id } = req.params;
        const body = (await req.json()) as { answers: Array<{ question_id: string; answer_text: string }> };

        const assessment = mockAssessments.find((a) => a.id === id);
        if (!assessment) {
          return res(
            ctx.status(404),
            ctx.json({ detail: "Assessment not found" })
          );
        }

        const updatedQuestions: AssessmentQuestion[] = [];

        // Update each answer
        body.answers.forEach(({ question_id, answer_text }) => {
          mockQuestionGroups = mockQuestionGroups.map(
            (group: typeof MOCK_CPRA_QUESTION_GROUPS[0]) => ({
              ...group,
              questions: group.questions.map((q: AssessmentQuestion) => {
                if (q.question_id === question_id || q.id === question_id) {
                  const updated = {
                    ...q,
                    answer_text,
                    answer_status: answer_text.trim() ? "complete" : "needs_input",
                    answer_source: "user_input",
                  } as AssessmentQuestion;
                  updatedQuestions.push(updated);
                  return updated;
                }
                return q;
              }),
            })
          );
        });

        // Recalculate completeness
        const completeness = calculateCompleteness(mockQuestionGroups);
        const status = determineStatus(completeness);

        // Update assessment
        const assessmentIndex = mockAssessments.findIndex((a) => a.id === id);
        mockAssessments[assessmentIndex] = {
          ...mockAssessments[assessmentIndex],
          completeness,
          status,
          updated_at: new Date().toISOString(),
        };

        const response: BulkUpdateAnswersResponse = {
          updated_count: updatedQuestions.length,
          completeness,
          status,
          questions: updatedQuestions,
        };

        return res(ctx.status(200), ctx.json(response));
      }
    ),

    // =========================================================================
    // GET /plus/privacy-assessments/:id/evidence - Get assessment evidence
    // =========================================================================
    rest.get(
      `${apiBase}/plus/privacy-assessments/:id/evidence`,
      (req, res, ctx) => {
        const { id } = req.params;
        const questionId = req.url.searchParams.get("question_id");
        const typeFilter = req.url.searchParams.get("type");
        const groupBy = req.url.searchParams.get("group_by");

        const assessment = mockAssessments.find((a) => a.id === id);
        if (!assessment) {
          return res(
            ctx.status(404),
            ctx.json({ detail: "Assessment not found" })
          );
        }

        let evidence = [...MOCK_EVIDENCE_ITEMS];

        // Filter by type if specified
        if (typeFilter) {
          evidence = evidence.filter((e) => e.type === typeFilter);
        }

        const response: AssessmentEvidenceResponse = {
          assessment_id: id as string,
          total_count: evidence.length,
        };

        // Group by question or type
        if (groupBy === "type") {
          response.by_type = {
            system: evidence.filter((e) => e.type === "system") as any[],
            ai_analysis: evidence.filter((e) => e.type === "ai_analysis") as any[],
            manual_entry: evidence.filter((e) => e.type === "manual_entry") as any[],
            slack_communication: evidence.filter(
              (e) => e.type === "slack_communication"
            ) as any[],
          };
        } else if (groupBy === "question") {
          response.by_question = {};
          mockQuestionGroups.forEach((group: typeof MOCK_CPRA_QUESTION_GROUPS[0]) => {
            group.questions.forEach((q: AssessmentQuestion) => {
              response.by_question![q.question_id] = {
                question_id: q.question_id,
                question_text: q.question_text,
                evidence: getEvidenceForGroup(group.id, evidence),
              };
            });
          });
        } else {
          response.items = evidence;
        }

        return res(ctx.status(200), ctx.json(response));
      }
    ),

    // =========================================================================
    // POST /plus/privacy-assessments/:id/questionnaire - Create questionnaire
    // =========================================================================
    rest.post(
      `${apiBase}/plus/privacy-assessments/:id/questionnaire`,
      async (req, res, ctx) => {
        const { id } = req.params;
        const body = (await req.json()) as CreateQuestionnaireRequest;

        const assessment = mockAssessments.find((a) => a.id === id);
        if (!assessment) {
          return res(
            ctx.status(404),
            ctx.json({ detail: "Assessment not found" })
          );
        }

        const sentAt = new Date().toISOString();

        // Create questionnaire status
        mockQuestionnaires[id as string] = {
          assessment_id: id as string,
          sent_at: sentAt,
          channel: body.channel,
          total_questions: MOCK_QUESTIONNAIRE_QUESTIONS.length,
          answered_questions: MOCK_QUESTIONNAIRE_QUESTIONS.filter(
            (q) => q.status === "answered"
          ).length,
          pending_questions: MOCK_QUESTIONNAIRE_QUESTIONS.filter(
            (q) => q.status === "pending"
          ).length,
          progress_percentage: Math.round(
            (MOCK_QUESTIONNAIRE_QUESTIONS.filter((q) => q.status === "answered")
              .length /
              MOCK_QUESTIONNAIRE_QUESTIONS.length) *
              100
          ),
          questions: MOCK_QUESTIONNAIRE_QUESTIONS,
          last_reminder_at: null,
          reminder_count: 0,
        };

        const response: QuestionnaireResponse = {
          sent_at: sentAt,
          channel: body.channel,
          questions_sent: MOCK_QUESTIONNAIRE_QUESTIONS.length,
          message_id: `slack-msg-${Date.now()}`,
        };

        return res(ctx.status(201), ctx.json(response));
      }
    ),

    // =========================================================================
    // GET /plus/privacy-assessments/:id/questionnaire - Get questionnaire status
    // =========================================================================
    rest.get(
      `${apiBase}/plus/privacy-assessments/:id/questionnaire`,
      (req, res, ctx) => {
        const { id } = req.params;

        const questionnaire = mockQuestionnaires[id as string];
        if (!questionnaire) {
          return res(
            ctx.status(404),
            ctx.json({ detail: "Questionnaire not found" })
          );
        }

        return res(ctx.status(200), ctx.json(questionnaire));
      }
    ),

    // =========================================================================
    // POST /plus/privacy-assessments/:id/questionnaire/reminders - Create reminder
    // =========================================================================
    rest.post(
      `${apiBase}/plus/privacy-assessments/:id/questionnaire/reminders`,
      async (req, res, ctx) => {
        const { id } = req.params;
        const body = ((await req.json()) as CreateReminderRequest) || {};

        const questionnaire = mockQuestionnaires[id as string];
        if (!questionnaire) {
          return res(
            ctx.status(404),
            ctx.json({ detail: "Questionnaire not found" })
          );
        }

        const sentAt = new Date().toISOString();

        // Update questionnaire with reminder info
        mockQuestionnaires[id as string] = {
          ...questionnaire,
          last_reminder_at: sentAt,
          reminder_count: questionnaire.reminder_count + 1,
        };

        const response: ReminderResponse = {
          sent_at: sentAt,
          channel: questionnaire.channel,
          pending_questions: questionnaire.pending_questions,
          message_id: `slack-reminder-${Date.now()}`,
        };

        return res(ctx.status(201), ctx.json(response));
      }
    ),
  ];
};
