import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import {
  AnswerSource,
  AnswerStatus,
  AssessmentStatus,
  PrivacyAssessmentDetailResponse,
  QuestionnaireSessionStatus,
  QuestionnaireStatus,
} from "./types";

// ── Mocks ──────────────────────────────────────────────────────────────

jest.mock("next/router", () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    pathname: "/",
    query: {},
    asPath: "/",
    isFallback: false,
  })),
}));

jest.mock("~/app/hooks", () => ({
  useAppSelector: () => ({
    email_address: "test@example.com",
    first_name: "Test",
    last_name: "User",
    username: "testuser",
    isRootUser: false,
  }),
  useAppDispatch: () => jest.fn(),
}));

jest.mock("~/features/auth", () => ({
  selectUser: jest.fn(),
}));

jest.mock("~/features/common/hooks/useTaxonomies", () => ({
  __esModule: true,
  default: () => ({
    getDataCategoryDisplayName: (key: string) => key,
  }),
}));

jest.mock("~/features/common/hooks/useRelativeTime", () => ({
  useRelativeTime: () => "5 minutes ago",
}));

jest.mock("~/features/common/helpers", () => ({
  getErrorMessage: jest.fn((e: unknown) => "Error"),
}));

const mockCreateQuestionnaire = jest.fn();
const mockCreateReminder = jest.fn();
const mockGetAssessmentConfigQuery = jest.fn();
const mockGetPrivacyAssessmentQuery = jest.fn();

jest.mock("./privacy-assessments.slice", () => ({
  useCreateQuestionnaireMutation: () => [
    mockCreateQuestionnaire,
    { isLoading: false },
  ],
  useCreateQuestionnaireReminderMutation: () => [
    mockCreateReminder,
    { isLoading: false },
  ],
  useGetAssessmentConfigQuery: () => mockGetAssessmentConfigQuery(),
  useGetPrivacyAssessmentQuery: () => mockGetPrivacyAssessmentQuery(),
  useStartQuestionnaireChatMutation: () => [jest.fn(), { isLoading: false }],
  useSendQuestionnaireChatReplyMutation: () => [
    jest.fn(),
    { isLoading: false },
  ],
  useGetQuestionnaireChatMessagesQuery: () => ({
    data: undefined,
    isLoading: false,
  }),
}));

const mockGetChatConfigsQuery = jest.fn();
jest.mock("../chat-provider/chatProvider.slice", () => ({
  useGetChatConfigsQuery: () => mockGetChatConfigsQuery(),
}));

jest.mock(
  "fidesui",
  () =>
    new Proxy(jest.requireActual("fidesui"), {
      get(target, prop) {
        if (prop === "useMessage") {
          return () => ({
            success: jest.fn(),
            error: jest.fn(),
            warning: jest.fn(),
          });
        }
        if (prop === "useNotification") {
          return () => ({
            success: jest.fn(),
            error: jest.fn(),
            warning: jest.fn(),
            info: jest.fn(),
          });
        }
        if (prop === "Drawer") {
          return ({
            open,
            children,
            title,
          }: {
            open: boolean;
            children: React.ReactNode;
            title?: string;
          }) =>
            open ? (
              <div data-testid="drawer">
                {title && <div>{title}</div>}
                {children}
              </div>
            ) : null;
        }
        if (prop === "Collapse") {
          return () => <div data-testid="collapse" />;
        }
        return target[prop as keyof typeof target];
      },
    }),
);

jest.mock("./QuestionnaireChat", () => {
  const MockChat = (props: {
    questionnaireId?: string;
    assessmentId: string;
  }) => (
    <div
      data-testid="questionnaire-chat"
      data-questionnaire-id={props.questionnaireId ?? ""}
      data-assessment-id={props.assessmentId}
    />
  );
  MockChat.displayName = "MockQuestionnaireChat";
  return { __esModule: true, default: MockChat };
});

jest.mock("./QuestionnaireStatusBar", () => ({
  QuestionnaireStatusBar: ({
    status,
    stopReason,
  }: {
    status: string;
    stopReason?: string | null;
  }) => (
    <div
      data-testid="questionnaire-status-bar"
      data-status={status}
      data-stop-reason={stopReason ?? ""}
    />
  ),
}));

jest.mock("./QuestionGroupPanel", () => ({
  QuestionGroupPanel: () => <div data-testid="question-group-panel" />,
}));

jest.mock("./EvidenceDrawer", () => ({
  EvidenceDrawer: () => null,
}));

jest.mock("./QuestionCard", () => ({
  QuestionCard: () => null,
}));

jest.mock("../common/logos/SlackLogo", () => ({
  SlackLogo: () => null,
}));

// ── Helpers ────────────────────────────────────────────────────────────

import { AssessmentDetail } from "./AssessmentDetail";

const makeQuestion = (overrides: Record<string, unknown> = {}) => ({
  id: "q-1",
  question_id: "qid-1",
  question_text: "What data do you process?",
  guidance: null,
  required: true,
  fides_sources: [],
  expected_coverage: "",
  answer_text: "",
  answer_status: AnswerStatus.NEEDS_INPUT,
  answer_source: AnswerSource.SYSTEM,
  confidence: null,
  evidence: [],
  missing_data: [],
  sme_prompt: null,
  ...overrides,
});

const makeAssessment = (
  overrides: Partial<PrivacyAssessmentDetailResponse> = {},
): PrivacyAssessmentDetailResponse => ({
  id: "assessment-1",
  name: "Test Assessment",
  status: AssessmentStatus.IN_PROGRESS,
  risk_level: null,
  assessment_type: "dpia",
  template_name: "DPIA Template",
  question_groups: [
    {
      id: "g-1",
      title: "Group 1",
      requirement_key: "rk-1",
      questions: [makeQuestion()],
      answered_count: 0,
      total_count: 1,
      risk_level: null,
      last_updated_at: null,
      last_updated_by: null,
    },
  ],
  questionnaire: null,
  metadata: null,
  data_categories: [],
  description: "",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  system_fides_key: "test-system",
  ...overrides,
});

const makeQuestionnaire = (
  overrides: Partial<QuestionnaireStatus> = {},
): QuestionnaireStatus => ({
  questionnaire_id: "qn-1",
  status: QuestionnaireSessionStatus.IN_PROGRESS,
  stop_reason: null,
  sent_at: "2026-01-01T12:00:00Z",
  channel: "fides",
  total_questions: 5,
  answered_questions: 2,
  last_reminder_at: null,
  reminder_count: 0,
  ...overrides,
});

// ── Setup ──────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
  mockGetAssessmentConfigQuery.mockReturnValue({
    data: { slack_channel_name: null },
    isLoading: false,
  });
  mockGetPrivacyAssessmentQuery.mockReturnValue({
    data: undefined,
    isLoading: false,
  });
  mockGetChatConfigsQuery.mockReturnValue({
    data: {
      items: [{ id: "cfg-1", provider_type: "fides", enabled: true }],
    },
    isLoading: false,
  });
});

// ── Tests ──────────────────────────────────────────────────────────────

describe("AssessmentDetail — Questionnaire button text", () => {
  it('shows "Start questionnaire" when no questionnaire exists', () => {
    render(<AssessmentDetail assessment={makeAssessment()} />);
    expect(
      screen.getByRole("button", { name: /start questionnaire/i }),
    ).toBeInTheDocument();
  });

  it('shows "Resume questionnaire" when questionnaire is in progress', () => {
    render(
      <AssessmentDetail
        assessment={makeAssessment({
          questionnaire: makeQuestionnaire({
            status: QuestionnaireSessionStatus.IN_PROGRESS,
          }),
        })}
      />,
    );
    expect(
      screen.getByRole("button", { name: /resume questionnaire/i }),
    ).toBeInTheDocument();
  });

  it('shows "Start questionnaire" when questionnaire is stopped', () => {
    render(
      <AssessmentDetail
        assessment={makeAssessment({
          questionnaire: makeQuestionnaire({
            status: QuestionnaireSessionStatus.STOPPED,
            stop_reason: "User requested stop",
          }),
        })}
      />,
    );
    expect(
      screen.getByRole("button", { name: /start questionnaire/i }),
    ).toBeInTheDocument();
  });
});

describe("AssessmentDetail — Status bar visibility", () => {
  it("hides status bar when no questionnaire", () => {
    render(<AssessmentDetail assessment={makeAssessment()} />);
    expect(
      screen.queryByTestId("questionnaire-status-bar"),
    ).not.toBeInTheDocument();
  });

  it("shows status bar when questionnaire has been sent", () => {
    render(
      <AssessmentDetail
        assessment={makeAssessment({
          questionnaire: makeQuestionnaire(),
        })}
      />,
    );
    expect(
      screen.getByTestId("questionnaire-status-bar"),
    ).toBeInTheDocument();
  });

  it("shows status bar with stopped status and stop reason", () => {
    render(
      <AssessmentDetail
        assessment={makeAssessment({
          questionnaire: makeQuestionnaire({
            status: QuestionnaireSessionStatus.STOPPED,
            stop_reason: "No longer needed",
          }),
        })}
      />,
    );
    const bar = screen.getByTestId("questionnaire-status-bar");
    expect(bar).toHaveAttribute("data-status", "stopped");
    expect(bar).toHaveAttribute("data-stop-reason", "No longer needed");
  });
});

describe("AssessmentDetail — Chat drawer and component props", () => {
  it("opens chat drawer when Start questionnaire is clicked", async () => {
    const user = userEvent.setup();
    render(<AssessmentDetail assessment={makeAssessment()} />);

    expect(screen.queryByTestId("drawer")).not.toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: /start questionnaire/i }),
    );

    expect(screen.getByTestId("drawer")).toBeInTheDocument();
    expect(screen.getByTestId("questionnaire-chat")).toBeInTheDocument();
  });

  it("passes questionnaireId when status is IN_PROGRESS", async () => {
    const user = userEvent.setup();
    render(
      <AssessmentDetail
        assessment={makeAssessment({
          questionnaire: makeQuestionnaire({
            questionnaire_id: "qn-active",
            status: QuestionnaireSessionStatus.IN_PROGRESS,
          }),
        })}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: /resume questionnaire/i }),
    );

    const chat = screen.getByTestId("questionnaire-chat");
    expect(chat).toHaveAttribute("data-questionnaire-id", "qn-active");
  });

  it("passes undefined questionnaireId when status is STOPPED (fresh start)", async () => {
    const user = userEvent.setup();
    render(
      <AssessmentDetail
        assessment={makeAssessment({
          questionnaire: makeQuestionnaire({
            questionnaire_id: "qn-old-stopped",
            status: QuestionnaireSessionStatus.STOPPED,
          }),
        })}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: /start questionnaire/i }),
    );

    const chat = screen.getByTestId("questionnaire-chat");
    expect(chat).toHaveAttribute("data-questionnaire-id", "");
  });
});
