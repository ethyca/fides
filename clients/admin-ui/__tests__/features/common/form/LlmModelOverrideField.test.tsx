import { fireEvent, screen, waitFor } from "@testing-library/react";
import { Form } from "fidesui";
import React from "react";

import { LlmModelOverrideField } from "../../../../src/features/common/form/LlmModelOverrideField";
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

// Wrapper component to provide Form context
const TestWrapper: React.FC<{
  children: React.ReactNode;
  initialValues?: Record<string, unknown>;
}> = ({ children, initialValues = {} }) => {
  const [form] = Form.useForm();
  return (
    <Form form={form} initialValues={initialValues}>
      {children}
    </Form>
  );
};

describe("LlmModelOverrideField", () => {
  describe("default behavior", () => {
    it("renders with default props", () => {
      render(
        <TestWrapper>
          <LlmModelOverrideField />
        </TestWrapper>,
      );

      expect(screen.getByText("LLM model override")).toBeInTheDocument();
      expect(screen.getByTestId("input-llm_model_override")).toBeInTheDocument();
    });

    it("renders with default test ID based on name", () => {
      render(
        <TestWrapper>
          <LlmModelOverrideField />
        </TestWrapper>,
      );

      const input = screen.getByTestId("input-llm_model_override");
      expect(input).toBeEnabled();
    });
  });

  describe("custom props", () => {
    it("renders with custom label", () => {
      render(
        <TestWrapper>
          <LlmModelOverrideField label="Custom Model" />
        </TestWrapper>,
      );

      expect(screen.getByText("Custom Model")).toBeInTheDocument();
    });

    it("renders with custom name and test ID", () => {
      render(
        <TestWrapper>
          <LlmModelOverrideField
            name="assessment_model_override"
            testId="assessment-model"
          />
        </TestWrapper>,
      );

      expect(screen.getByTestId("input-assessment-model")).toBeInTheDocument();
    });

    it("renders with placeholder", () => {
      render(
        <TestWrapper>
          <LlmModelOverrideField placeholder="gpt-4-turbo" />
        </TestWrapper>,
      );

      const input = screen.getByTestId("input-llm_model_override");
      expect(input).toHaveAttribute("placeholder", "gpt-4-turbo");
    });
  });

  describe("disabled state", () => {
    it("disables input when disabled prop is true", () => {
      render(
        <TestWrapper>
          <LlmModelOverrideField disabled />
        </TestWrapper>,
      );

      const input = screen.getByTestId("input-llm_model_override");
      expect(input).toBeDisabled();
    });

    it("shows disabled tooltip when disabled with disabledTooltip", async () => {
      render(
        <TestWrapper>
          <LlmModelOverrideField
            disabled
            disabledTooltip="LLM is not enabled on this server"
          />
        </TestWrapper>,
      );

      // The label should be wrapped in a tooltip
      const labelText = screen.getByText("LLM model override");
      expect(labelText.closest("span")).toBeInTheDocument();
    });
  });

  describe("form integration", () => {
    it("can receive initial value from form", () => {
      render(
        <TestWrapper initialValues={{ llm_model_override: "custom-model" }}>
          <LlmModelOverrideField />
        </TestWrapper>,
      );

      const input = screen.getByTestId("input-llm_model_override");
      expect(input).toHaveValue("custom-model");
    });

    it("allows user to type in the input", async () => {
      render(
        <TestWrapper>
          <LlmModelOverrideField />
        </TestWrapper>,
      );

      const input = screen.getByTestId("input-llm_model_override");
      fireEvent.change(input, { target: { value: "openai/gpt-4" } });

      await waitFor(() => {
        expect(input).toHaveValue("openai/gpt-4");
      });
    });
  });

  describe("use cases", () => {
    it("works for website monitor config", () => {
      render(
        <TestWrapper>
          <LlmModelOverrideField
            disabled={false}
            placeholder="e.g., openrouter/google/gemini-2.5-flash"
            tooltip="Optionally specify a custom model to use for LLM classification of website assets"
          />
        </TestWrapper>,
      );

      const input = screen.getByTestId("input-llm_model_override");
      expect(input).toBeEnabled();
      expect(input).toHaveAttribute(
        "placeholder",
        "e.g., openrouter/google/gemini-2.5-flash",
      );
    });

    it("works for database monitor config", () => {
      render(
        <TestWrapper>
          <LlmModelOverrideField
            label="Model override"
            tooltip="Optionally specify a custom model to use for LLM classification"
          />
        </TestWrapper>,
      );

      expect(screen.getByText("Model override")).toBeInTheDocument();
    });

    it("works for privacy assessment settings", () => {
      render(
        <TestWrapper>
          <LlmModelOverrideField
            name="assessment_model_override"
            label="Assessment model"
            testId="assessment-model"
            placeholder="default-assessment-model"
            tooltip="Custom LLM model for running privacy assessments. Leave empty to use the default."
          />
        </TestWrapper>,
      );

      expect(screen.getByText("Assessment model")).toBeInTheDocument();
      const input = screen.getByTestId("input-assessment-model");
      expect(input).toHaveAttribute("placeholder", "default-assessment-model");
    });
  });
});
