import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { parseCronExpression } from "~/features/digests/helpers/cronHelpers";

import AssessmentSettingsModal from "./AssessmentSettingsModal";

// Mock fidesui components - only mock Select to make it testable
jest.mock(
  "fidesui",
  () =>
    new Proxy(jest.requireActual("fidesui"), {
      get(target, prop) {
        if (prop === "Select") {
          const MockAntSelect = ({
            value,
            onChange,
            options,
            ...props
          }: any) => (
            <select
              {...props}
              value={value || ""}
              onChange={(e) => onChange?.(e.target.value || null)}
            >
              <option value="">Select...</option>
              {options?.map((opt: any) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          );
          MockAntSelect.displayName = "MockAntSelect";
          return MockAntSelect;
        }
        if (prop === "useMessage") {
          return () => ({
            success: jest.fn(),
            error: jest.fn(),
            warning: jest.fn(),
          });
        }
        return target[prop as keyof typeof target];
      },
    }),
);

// Mock RTK Query hooks
const mockConfig = {
  id: "config-1",
  assessment_model_override: null,
  chat_model_override: null,
  reassessment_enabled: false,
  reassessment_cron: "0 9 * * *",
  slack_channel_id: null,
  slack_channel_name: null,
  effective_assessment_model: "openrouter/anthropic/claude-opus-4",
  effective_chat_model: "openrouter/google/gemini-2.5-flash",
};

const mockDefaults = {
  default_assessment_model: "openrouter/anthropic/claude-opus-4",
  default_chat_model: "openrouter/google/gemini-2.5-flash",
  default_reassessment_cron: "0 9 * * *",
};

const mockGetAssessmentConfigQuery = jest.fn();
const mockGetAssessmentConfigDefaultsQuery = jest.fn();
const mockUpdateAssessmentConfigMutation = jest.fn();
const mockTestSlackChannelMutation = jest.fn();

jest.mock("./privacy-assessments.slice", () => ({
  useGetAssessmentConfigQuery: () => mockGetAssessmentConfigQuery(),
  useGetAssessmentConfigDefaultsQuery: () =>
    mockGetAssessmentConfigDefaultsQuery(),
  useUpdateAssessmentConfigMutation: () => [
    mockUpdateAssessmentConfigMutation(),
    { isLoading: false },
  ],
  useTestSlackChannelMutation: () => [
    mockTestSlackChannelMutation(),
    { isLoading: false },
  ],
}));

const mockGetChatChannelsQuery = jest.fn();
jest.mock("~/features/chat-provider/chatProvider.slice", () => ({
  useGetChatChannelsQuery: () => mockGetChatChannelsQuery(),
}));

jest.mock("~/features/common/hooks", () => ({
  useAPIHelper: () => ({ handleError: jest.fn() }),
}));

describe("AssessmentSettingsModal", () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockGetAssessmentConfigQuery.mockReturnValue({
      data: mockConfig,
      isLoading: false,
      refetch: jest.fn(),
    });
    mockGetAssessmentConfigDefaultsQuery.mockReturnValue({
      data: mockDefaults,
    });
    mockGetChatChannelsQuery.mockReturnValue({
      data: { channels: [] },
      isLoading: false,
      refetch: jest.fn(),
    });
    mockUpdateAssessmentConfigMutation.mockReturnValue(jest.fn());
    mockTestSlackChannelMutation.mockReturnValue(jest.fn());
  });

  describe("Frequency preset handling", () => {
    it("shows custom cron input when custom preset is selected", async () => {
      const user = userEvent.setup();
      render(<AssessmentSettingsModal open onClose={mockOnClose} />);

      // Enable reassessment
      const enableSwitch = screen.getByTestId("switch-reassessment-enabled");
      await user.click(enableSwitch);

      // Initially cron input should not be visible (preset selected)
      expect(screen.queryByTestId("input-cron")).not.toBeInTheDocument();

      // Select custom frequency
      const frequencySelect = screen.getByTestId("select-frequency");
      await user.selectOptions(frequencySelect, "custom");

      // Now cron input should be visible
      expect(screen.getByTestId("input-cron")).toBeInTheDocument();
    });

    it("hides cron input when switching from custom to preset", async () => {
      const user = userEvent.setup();

      // Start with a custom cron config
      mockGetAssessmentConfigQuery.mockReturnValue({
        data: {
          ...mockConfig,
          reassessment_enabled: true,
          reassessment_cron: "0 0 15 * *",
        },
        isLoading: false,
        refetch: jest.fn(),
      });

      render(<AssessmentSettingsModal open onClose={mockOnClose} />);

      // Custom cron should trigger custom mode, showing the input
      await waitFor(() => {
        expect(screen.getByTestId("input-cron")).toBeInTheDocument();
      });

      // Select a preset frequency
      const frequencySelect = screen.getByTestId("select-frequency");
      await user.selectOptions(frequencySelect, "daily");

      // Cron input should be hidden
      await waitFor(() => {
        expect(screen.queryByTestId("input-cron")).not.toBeInTheDocument();
      });
    });
  });

  describe("Modal rendering", () => {
    it("renders the modal title", () => {
      render(<AssessmentSettingsModal open onClose={mockOnClose} />);
      expect(screen.getByText("Assessment Settings")).toBeInTheDocument();
    });

    it("renders LLM configuration inputs", () => {
      render(<AssessmentSettingsModal open onClose={mockOnClose} />);
      expect(screen.getByTestId("input-assessment-model")).toBeInTheDocument();
      expect(screen.getByTestId("input-chat-model")).toBeInTheDocument();
    });

    it("renders save and cancel buttons", () => {
      render(<AssessmentSettingsModal open onClose={mockOnClose} />);
      expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /cancel/i }),
      ).toBeInTheDocument();
    });
  });
});

/**
 * Tests for the cron expression validation logic used by AssessmentSettingsModal.
 * These tests validate the parseCronExpression function directly, which is the
 * core validation logic. Testing the function directly is more reliable than
 * testing through the form UI due to antd's complex async form validation.
 */
describe("parseCronExpression validation", () => {
  describe("valid expressions", () => {
    it("returns config for valid daily cron", () => {
      const result = parseCronExpression("0 9 * * *");
      expect(result).not.toBeNull();
    });

    it("returns config for valid weekly cron", () => {
      const result = parseCronExpression("0 9 * * 1");
      expect(result).not.toBeNull();
    });

    it("returns config for valid monthly cron", () => {
      const result = parseCronExpression("0 9 1 * *");
      expect(result).not.toBeNull();
    });
  });

  describe("invalid expressions", () => {
    it("returns null for cron with too few parts", () => {
      expect(parseCronExpression("0 9 *")).toBeNull();
    });

    it("returns null for cron with too many parts", () => {
      expect(parseCronExpression("0 9 * * * *")).toBeNull();
    });

    it("returns null for invalid minute value (60)", () => {
      expect(parseCronExpression("60 9 * * *")).toBeNull();
    });

    it("returns null for negative minute value", () => {
      expect(parseCronExpression("-1 9 * * *")).toBeNull();
    });

    it("returns null for invalid hour value (25)", () => {
      expect(parseCronExpression("0 25 * * *")).toBeNull();
    });
  });
});
