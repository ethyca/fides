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
  reassessment_timezone: "UTC",
  slack_channel_id: null,
  slack_channel_name: null,
  effective_assessment_model: "openrouter/anthropic/claude-opus-4",
  effective_chat_model: "openrouter/google/gemini-2.5-flash",
};

const mockDefaults = {
  default_assessment_model: "openrouter/anthropic/claude-opus-4",
  default_chat_model: "openrouter/google/gemini-2.5-flash",
  default_reassessment_cron: "0 9 * * *",
  default_reassessment_timezone: "UTC",
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

  describe("Cron validation", () => {
    it("accepts valid cron expressions", async () => {
      const user = userEvent.setup();
      render(<AssessmentSettingsModal open onClose={mockOnClose} />);

      // Enable reassessment to show schedule options
      const enableSwitch = screen.getByTestId("switch-reassessment-enabled");
      await user.click(enableSwitch);

      // Select custom frequency to show cron input
      const frequencySelect = screen.getByTestId("select-frequency");
      await user.selectOptions(frequencySelect, "custom");

      // Enter a valid cron expression
      const cronInput = screen.getByTestId("input-cron");
      await user.clear(cronInput);
      await user.type(cronInput, "0 9 * * 1");

      // Trigger validation by blurring
      await user.tab();

      // Wait for validation - should not show error
      await waitFor(() => {
        expect(
          screen.queryByText(/invalid cron expression/i),
        ).not.toBeInTheDocument();
      });
    });

    it("rejects invalid cron expressions with too few parts", async () => {
      const user = userEvent.setup();
      render(<AssessmentSettingsModal open onClose={mockOnClose} />);

      // Enable reassessment
      const enableSwitch = screen.getByTestId("switch-reassessment-enabled");
      await user.click(enableSwitch);

      // Select custom frequency
      const frequencySelect = screen.getByTestId("select-frequency");
      await user.selectOptions(frequencySelect, "custom");

      // Enter an invalid cron expression (only 3 parts)
      const cronInput = screen.getByTestId("input-cron");
      await user.clear(cronInput);
      await user.type(cronInput, "0 9 *");

      // Click save to trigger validation
      const saveButton = screen.getByRole("button", { name: /save/i });
      await user.click(saveButton);

      // Should show error
      await waitFor(() => {
        expect(
          screen.getByText(/invalid cron expression/i),
        ).toBeInTheDocument();
      });
    });

    it("rejects invalid cron expressions with invalid values", async () => {
      const user = userEvent.setup();
      render(<AssessmentSettingsModal open onClose={mockOnClose} />);

      // Enable reassessment
      const enableSwitch = screen.getByTestId("switch-reassessment-enabled");
      await user.click(enableSwitch);

      // Select custom frequency
      const frequencySelect = screen.getByTestId("select-frequency");
      await user.selectOptions(frequencySelect, "custom");

      // Enter a cron with invalid minute value (99)
      const cronInput = screen.getByTestId("input-cron");
      await user.clear(cronInput);
      await user.type(cronInput, "99 9 * * *");

      // Click save to trigger validation
      const saveButton = screen.getByRole("button", { name: /save/i });
      await user.click(saveButton);

      // Should show error
      await waitFor(() => {
        expect(
          screen.getByText(/invalid cron expression/i),
        ).toBeInTheDocument();
      });
    });
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
});

describe("parseCronExpression validation", () => {
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

  it("returns null for invalid cron with wrong part count", () => {
    expect(parseCronExpression("0 9 *")).toBeNull();
    expect(parseCronExpression("0 9 * * * *")).toBeNull();
  });

  it("returns null for invalid minute value", () => {
    expect(parseCronExpression("60 9 * * *")).toBeNull();
    expect(parseCronExpression("-1 9 * * *")).toBeNull();
  });

  it("returns null for invalid hour value", () => {
    expect(parseCronExpression("0 25 * * *")).toBeNull();
  });
});
