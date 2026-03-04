import { screen } from "@testing-library/react";
import { Form } from "fidesui";
import React from "react";

import { LlmModelSelector } from "../../../../src/features/common/form/LlmModelSelector";
import { render } from "../../../utils/test-utils";

// Mock ESM-only packages to avoid Jest import issues
jest.mock("query-string", () => ({
  __esModule: true,
  default: { stringify: jest.fn(), parse: jest.fn() },
}));

jest.mock("react-dnd", () => ({
  useDrag: jest.fn(() => [{}, jest.fn()]),
  useDrop: jest.fn(() => [{}, jest.fn()]),
  DndProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock nuqs
// eslint-disable-next-line global-require
jest.mock("nuqs", () => require("../../../utils/nuqs-mock").nuqsMock);

// Mock the config settings query
const mockUseGetConfigurationSettingsQuery = jest.fn();
jest.mock(
  "../../../../src/features/config-settings/config-settings.slice",
  () => ({
    useGetConfigurationSettingsQuery: (...args: unknown[]) =>
      mockUseGetConfigurationSettingsQuery(...args),
  }),
);

// Wrapper component to provide Form context
const TestWrapper = ({
  children,
  initialValues = {},
}: {
  children: React.ReactNode;
  initialValues?: Record<string, unknown>;
}) => {
  const [form] = Form.useForm();
  return (
    <Form form={form} initialValues={initialValues}>
      {children}
    </Form>
  );
};

describe("LlmModelSelector", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("when skip is true", () => {
    it("renders nothing", () => {
      mockUseGetConfigurationSettingsQuery.mockReturnValue({ data: null });

      const { container } = render(
        <TestWrapper>
          <LlmModelSelector skip useLlmClassifier={false} />
        </TestWrapper>,
      );

      expect(container.querySelector("form")?.children.length).toBe(0);
    });

    it("skips the config query", () => {
      mockUseGetConfigurationSettingsQuery.mockReturnValue({ data: null });

      render(
        <TestWrapper>
          <LlmModelSelector skip useLlmClassifier={false} />
        </TestWrapper>,
      );

      expect(mockUseGetConfigurationSettingsQuery).toHaveBeenCalledWith(
        { api_set: false },
        { skip: true },
      );
    });
  });

  describe("when server supports LLM classifier", () => {
    beforeEach(() => {
      mockUseGetConfigurationSettingsQuery.mockReturnValue({
        data: {
          detection_discovery: {
            llm_classifier_enabled: true,
          },
        },
      });
    });

    it("renders enabled switch", () => {
      render(
        <TestWrapper>
          <LlmModelSelector useLlmClassifier={false} />
        </TestWrapper>,
      );

      const switchElement = screen.getByTestId("input-use_llm_classifier");
      expect(switchElement).toBeInTheDocument();
      expect(switchElement).not.toBeDisabled();
    });

    it("does not show model override when switch is off", () => {
      render(
        <TestWrapper>
          <LlmModelSelector useLlmClassifier={false} />
        </TestWrapper>,
      );

      expect(
        screen.queryByTestId("input-llm_model_override"),
      ).not.toBeInTheDocument();
    });

    it("shows model override field when switch is on", () => {
      render(
        <TestWrapper initialValues={{ use_llm_classifier: true }}>
          <LlmModelSelector useLlmClassifier />
        </TestWrapper>,
      );

      const input = screen.getByTestId("input-llm_model_override");
      expect(input).toBeInTheDocument();
      expect(input).not.toBeDisabled();
    });

    it("renders with custom field names", () => {
      render(
        <TestWrapper>
          <LlmModelSelector
            useLlmClassifier
            switchName="enable_llm"
            modelOverrideName="custom_model"
          />
        </TestWrapper>,
      );

      expect(screen.getByTestId("input-enable_llm")).toBeInTheDocument();
      expect(screen.getByTestId("input-custom_model")).toBeInTheDocument();
    });

    it("renders with placeholder", () => {
      render(
        <TestWrapper>
          <LlmModelSelector
            useLlmClassifier
            modelOverridePlaceholder="e.g., openrouter/google/gemini-2.5-flash"
          />
        </TestWrapper>,
      );

      const input = screen.getByTestId("input-llm_model_override");
      expect(input).toHaveAttribute(
        "placeholder",
        "e.g., openrouter/google/gemini-2.5-flash",
      );
    });
  });

  describe("when server does not support LLM classifier", () => {
    beforeEach(() => {
      mockUseGetConfigurationSettingsQuery.mockReturnValue({
        data: {
          detection_discovery: {
            llm_classifier_enabled: false,
          },
        },
      });
    });

    it("renders disabled switch", () => {
      render(
        <TestWrapper>
          <LlmModelSelector useLlmClassifier={false} />
        </TestWrapper>,
      );

      const switchElement = screen.getByTestId("input-use_llm_classifier");
      expect(switchElement).toBeInTheDocument();
      expect(switchElement).toBeDisabled();
    });

    it("hides model override field even when useLlmClassifier prop is true", () => {
      // When server doesn't support LLM, we don't show the model field
      // even if the prop says it should be on (the component resets the form value)
      render(
        <TestWrapper initialValues={{ use_llm_classifier: true }}>
          <LlmModelSelector useLlmClassifier />
        </TestWrapper>,
      );

      expect(
        screen.queryByTestId("input-llm_model_override"),
      ).not.toBeInTheDocument();
    });
  });

  describe("when config is loading", () => {
    it("renders disabled switch while loading", () => {
      mockUseGetConfigurationSettingsQuery.mockReturnValue({
        data: undefined,
        isLoading: true,
      });

      render(
        <TestWrapper>
          <LlmModelSelector useLlmClassifier={false} />
        </TestWrapper>,
      );

      const switchElement = screen.getByTestId("input-use_llm_classifier");
      expect(switchElement).toBeDisabled();
    });
  });

  describe("use cases", () => {
    beforeEach(() => {
      mockUseGetConfigurationSettingsQuery.mockReturnValue({
        data: {
          detection_discovery: {
            llm_classifier_enabled: true,
          },
        },
      });
    });

    it("works for website monitor", () => {
      render(
        <TestWrapper>
          <LlmModelSelector
            useLlmClassifier
            modelOverridePlaceholder="e.g., openrouter/google/gemini-2.5-flash"
          />
        </TestWrapper>,
      );

      expect(
        screen.getByTestId("input-use_llm_classifier"),
      ).toBeInTheDocument();
      expect(
        screen.getByTestId("input-llm_model_override"),
      ).toBeInTheDocument();
    });

    it("works for database monitor", () => {
      render(
        <TestWrapper>
          <LlmModelSelector useLlmClassifier />
        </TestWrapper>,
      );

      expect(
        screen.getByTestId("input-use_llm_classifier"),
      ).toBeInTheDocument();
      expect(
        screen.getByTestId("input-llm_model_override"),
      ).toBeInTheDocument();
    });
  });

  describe("when showSwitch is false", () => {
    beforeEach(() => {
      mockUseGetConfigurationSettingsQuery.mockReturnValue({
        data: {
          detection_discovery: {
            llm_classifier_enabled: true,
          },
        },
      });
    });

    it("does not render the switch", () => {
      render(
        <TestWrapper>
          <LlmModelSelector showSwitch={false} />
        </TestWrapper>,
      );

      expect(
        screen.queryByTestId("input-use_llm_classifier"),
      ).not.toBeInTheDocument();
    });

    it("always shows the model override field", () => {
      render(
        <TestWrapper>
          <LlmModelSelector showSwitch={false} />
        </TestWrapper>,
      );

      expect(
        screen.getByTestId("input-llm_model_override"),
      ).toBeInTheDocument();
    });

    it("renders with custom label and tooltip", () => {
      render(
        <TestWrapper>
          <LlmModelSelector
            showSwitch={false}
            modelOverrideLabel="Assessment model"
            modelOverrideTooltip="Custom tooltip"
          />
        </TestWrapper>,
      );

      expect(screen.getByText("Assessment model")).toBeInTheDocument();
    });

    it("renders with custom test ID", () => {
      render(
        <TestWrapper>
          <LlmModelSelector
            showSwitch={false}
            modelOverrideName="assessment_model_override"
            modelOverrideTestId="assessment-model"
          />
        </TestWrapper>,
      );

      expect(screen.getByTestId("input-assessment-model")).toBeInTheDocument();
    });

    it("works for privacy assessment settings", () => {
      render(
        <TestWrapper>
          <LlmModelSelector
            showSwitch={false}
            modelOverrideName="assessment_model_override"
            modelOverrideLabel="Assessment model"
            modelOverrideTestId="assessment-model"
            modelOverridePlaceholder="default-model"
          />
        </TestWrapper>,
      );

      expect(screen.getByText("Assessment model")).toBeInTheDocument();
      const input = screen.getByTestId("input-assessment-model");
      expect(input).toHaveAttribute("placeholder", "default-model");
      expect(input).toBeEnabled();
    });
  });
});
