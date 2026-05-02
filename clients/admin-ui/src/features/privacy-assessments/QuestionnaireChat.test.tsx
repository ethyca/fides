import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";

// ── Mocks ──────────────────────────────────────────────────────────────

jest.mock("~/features/common/helpers", () => ({
  getErrorMessage: jest.fn(() => "Error"),
}));

jest.mock("~/features/common/Image", () => {
  const MockImage = () => <span data-testid="image" />;
  MockImage.displayName = "MockImage";
  return { __esModule: true, default: MockImage };
});

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
        if (prop === "Bubble") {
          const BubbleList = ({
            items,
          }: {
            items: { key: string; role: string; content: string }[];
          }) => (
            <div data-testid="bubble-list">
              {items.map((item) => (
                <div key={item.key} data-testid={`msg-${item.role}`}>
                  {item.content}
                </div>
              ))}
            </div>
          );
          return { List: BubbleList };
        }
        if (prop === "Sender") {
          return ({
            onSubmit,
            disabled,
            value,
            onChange,
          }: {
            onSubmit: (v: string) => void;
            disabled: boolean;
            value: string;
            onChange: (v: string) => void;
          }) => (
            <div data-testid="sender">
              <input
                data-testid="sender-input"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                disabled={disabled}
              />
              <button
                data-testid="sender-submit"
                onClick={() => onSubmit(value)}
                disabled={disabled}
                type="button"
              >
                Send
              </button>
            </div>
          );
        }
        return target[prop as keyof typeof target];
      },
    }),
);

const mockStartChat = jest.fn();
const mockSendReply = jest.fn();
const mockGetMessages = jest.fn();

jest.mock("./privacy-assessments.slice", () => ({
  useStartQuestionnaireChatMutation: () => [
    mockStartChat,
    { isLoading: false },
  ],
  useSendQuestionnaireChatReplyMutation: () => [
    mockSendReply,
    { isLoading: false },
  ],
  useGetQuestionnaireChatMessagesQuery: (...args: unknown[]) =>
    mockGetMessages(...args),
}));

// ── Helpers ────────────────────────────────────────────────────────────

import QuestionnaireChat from "./QuestionnaireChat";

const defaultProps = {
  assessmentId: "assessment-1",
  userEmail: "user@example.com",
  userName: "Test User",
};

beforeEach(() => {
  jest.clearAllMocks();

  mockGetMessages.mockReturnValue({
    data: undefined,
    isLoading: false,
  });

  mockStartChat.mockReturnValue({
    unwrap: () =>
      Promise.resolve({
        questionnaire_id: "qn-new",
        assessment_id: "assessment-1",
        messages: [
          { text: "Welcome!", is_bot_message: true, sender_email: null },
        ],
        total_questions: 3,
      }),
  });

  mockSendReply.mockReturnValue({
    unwrap: () =>
      Promise.resolve({
        bot_messages: [
          { text: "Thanks for your answer.", is_bot_message: true },
        ],
        status: "in_progress",
        answered_questions: 1,
        total_questions: 3,
      }),
  });
});

// ── Tests ──────────────────────────────────────────────────────────────

describe("QuestionnaireChat — new session", () => {
  it("calls startChat exactly once (no double-fire)", async () => {
    render(<QuestionnaireChat {...defaultProps} />);

    await waitFor(() => {
      expect(mockStartChat).toHaveBeenCalledTimes(1);
    });

    expect(mockStartChat).toHaveBeenCalledWith({
      assessment_id: "assessment-1",
      user_email: "user@example.com",
    });
  });

  it("renders bot messages from startChat response", async () => {
    render(<QuestionnaireChat {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Welcome!")).toBeInTheDocument();
    });
  });
});

describe("QuestionnaireChat — resume session", () => {
  it("does not call startChat when questionnaireId is provided", async () => {
    mockGetMessages.mockReturnValue({
      data: [
        {
          text: "What data do you process?",
          is_bot_message: true,
          sender_email: null,
          timestamp: null,
          question_index: 0,
        },
        {
          text: "We process email addresses",
          is_bot_message: false,
          sender_email: "user@example.com",
          timestamp: null,
          question_index: 0,
        },
        {
          text: "Got it, thanks!",
          is_bot_message: true,
          sender_email: null,
          timestamp: null,
          question_index: 0,
        },
      ],
      isLoading: false,
    });

    render(
      <QuestionnaireChat {...defaultProps} questionnaireId="qn-existing" />,
    );

    await waitFor(() => {
      expect(screen.getByText("We process email addresses")).toBeInTheDocument();
    });

    expect(mockStartChat).not.toHaveBeenCalled();
  });

  it("renders both user and bot messages from backend", async () => {
    mockGetMessages.mockReturnValue({
      data: [
        {
          text: "Question 1?",
          is_bot_message: true,
          sender_email: null,
          timestamp: null,
          question_index: 0,
        },
        {
          text: "My answer",
          is_bot_message: false,
          sender_email: "user@example.com",
          timestamp: null,
          question_index: 0,
        },
      ],
      isLoading: false,
    });

    render(
      <QuestionnaireChat {...defaultProps} questionnaireId="qn-existing" />,
    );

    await waitFor(() => {
      expect(screen.getByText("Question 1?")).toBeInTheDocument();
      expect(screen.getByText("My answer")).toBeInTheDocument();
    });

    const aiMessages = screen.getAllByTestId("msg-ai");
    const userMessages = screen.getAllByTestId("msg-user");
    expect(aiMessages).toHaveLength(1);
    expect(userMessages).toHaveLength(1);
  });
});

describe("QuestionnaireChat — sending messages", () => {
  it("adds user message optimistically and appends bot response", async () => {
    mockGetMessages.mockReturnValue({
      data: [
        {
          text: "What data?",
          is_bot_message: true,
          sender_email: null,
          timestamp: null,
          question_index: 0,
        },
      ],
      isLoading: false,
    });

    render(
      <QuestionnaireChat {...defaultProps} questionnaireId="qn-existing" />,
    );

    await waitFor(() => {
      expect(screen.getByText("What data?")).toBeInTheDocument();
    });

    const input = screen.getByTestId("sender-input");
    fireEvent.change(input, { target: { value: "Email addresses" } });

    await act(async () => {
      fireEvent.click(screen.getByTestId("sender-submit"));
    });

    await waitFor(() => {
      expect(screen.getByText("Email addresses")).toBeInTheDocument();
      expect(
        screen.getByText("Thanks for your answer."),
      ).toBeInTheDocument();
    });

    expect(mockSendReply).toHaveBeenCalledWith(
      expect.objectContaining({
        assessment_id: "assessment-1",
        questionnaire_id: "qn-existing",
        message_text: "Email addresses",
        user_email: "user@example.com",
      }),
    );
  });

  it("shows progress after receiving reply", async () => {
    mockGetMessages.mockReturnValue({
      data: [
        {
          text: "Question?",
          is_bot_message: true,
          sender_email: null,
          timestamp: null,
          question_index: 0,
        },
      ],
      isLoading: false,
    });

    render(
      <QuestionnaireChat {...defaultProps} questionnaireId="qn-existing" />,
    );

    await waitFor(() => {
      expect(screen.getByText("Question?")).toBeInTheDocument();
    });

    const input = screen.getByTestId("sender-input");
    fireEvent.change(input, { target: { value: "Answer" } });

    await act(async () => {
      fireEvent.click(screen.getByTestId("sender-submit"));
    });

    await waitFor(() => {
      expect(screen.getByText("1/3 answered")).toBeInTheDocument();
    });
  });
});
