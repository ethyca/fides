import { render, screen } from "@testing-library/react";
import React from "react";

import JiraConfigTab from "~/features/integrations/configure-jira/JiraConfigTab";
import {
  AccessLevel,
  ConnectionConfigurationResponse,
  ConnectionType,
} from "~/types/api";

// Mock all RTK query hooks used by JiraConfigTab
const mockUseGetJiraProjectsQuery = jest.fn();
const mockUseGetJiraIssueTypesQuery = jest.fn();
const mockUseGetJiraStatusesQuery = jest.fn();
const mockUseGetJiraTemplateVariablesQuery = jest.fn();
const mockUsePreviewJiraTicketMutation = jest.fn();

jest.mock("~/features/plus/plus.slice", () => ({
  useGetJiraProjectsQuery: (...args: unknown[]) =>
    mockUseGetJiraProjectsQuery(...args),
  useGetJiraIssueTypesQuery: (...args: unknown[]) =>
    mockUseGetJiraIssueTypesQuery(...args),
  useGetJiraStatusesQuery: (...args: unknown[]) =>
    mockUseGetJiraStatusesQuery(...args),
  useGetJiraTemplateVariablesQuery: (...args: unknown[]) =>
    mockUseGetJiraTemplateVariablesQuery(...args),
  usePreviewJiraTicketMutation: () => mockUsePreviewJiraTicketMutation(),
}));

jest.mock("~/features/datastore-connections", () => ({
  usePatchDatastoreConnectionSecretsMutation: () => [
    jest.fn(),
    { isLoading: false },
  ],
}));

// Stub fidesui — provide just the components JiraConfigTab uses
jest.mock("fidesui", () => ({
  Alert: ({
    message,
    description,
    action,
    showIcon: _showIcon,
    type: _type,
    ...props
  }: Record<string, unknown>) => (
    <div data-testid="alert" {...props}>
      <span>{message as string}</span>
      <span>{description as string}</span>
      {action as React.ReactNode}
    </div>
  ),
  Button: ({
    children,
    htmlType,
    loading: _loading,
    ...props
  }: Record<string, unknown>) => (
    <button
      // eslint-disable-next-line react/button-has-type
      type={(htmlType as "button" | "submit" | "reset" | undefined) ?? "button"}
      {...props}
    >
      {children as React.ReactNode}
    </button>
  ),
  Flex: ({ children }: Record<string, unknown>) => (
    <div>{children as React.ReactNode}</div>
  ),
  Form: Object.assign(
    ({ children }: Record<string, unknown>) => (
      <form>{children as React.ReactNode}</form>
    ),
    {
      useForm: () => [{ setFieldValue: jest.fn() }],
      useWatch: () => undefined,
      Item: ({
        children,
        label,
      }: {
        children?: React.ReactNode;
        label?: React.ReactNode;
      }) => (
        <div>
          {label && <label>{label}</label>}
          {children}
        </div>
      ),
    },
  ),
  Modal: ({ children, open }: Record<string, unknown>) =>
    open ? <div>{children as React.ReactNode}</div> : null,
  Select: () => <select aria-label="mock-select" />,
  Typography: {
    Paragraph: ({ children }: Record<string, unknown>) => (
      <p>{children as React.ReactNode}</p>
    ),
    Text: ({ children }: Record<string, unknown>) => (
      <span>{children as React.ReactNode}</span>
    ),
  },
  useMessage: () => ({
    success: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
  }),
}));

// Stub the TemplateVariableInput since it has internal deps we don't need
jest.mock("~/features/common/TemplateVariableInput", () => ({
  __esModule: true,
  default: (props: { rows?: number; placeholder?: string }) => (
    <textarea data-testid="template-input" placeholder={props.placeholder} />
  ),
}));

const mockConnection: ConnectionConfigurationResponse = {
  key: "jira-test",
  name: "Jira Test",
  connection_type: ConnectionType.JIRA_TICKET,
  access: AccessLevel.WRITE,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  disabled: false,
  saas_config: undefined,
  secrets: {},
};

const defaultQueryReturn = {
  data: undefined,
  isLoading: false,
  error: undefined,
};

beforeEach(() => {
  mockUseGetJiraProjectsQuery.mockReturnValue(defaultQueryReturn);
  mockUseGetJiraIssueTypesQuery.mockReturnValue(defaultQueryReturn);
  mockUseGetJiraStatusesQuery.mockReturnValue(defaultQueryReturn);
  mockUseGetJiraTemplateVariablesQuery.mockReturnValue(defaultQueryReturn);
  mockUsePreviewJiraTicketMutation.mockReturnValue([
    jest.fn(),
    { isLoading: false },
  ]);
});

describe("JiraConfigTab", () => {
  it("renders the configuration form when there is no error", () => {
    render(<JiraConfigTab connection={mockConnection} />);
    expect(screen.getByText(/configure how fides creates/i)).toBeTruthy();
    expect(screen.queryByText(/jira authorization expired/i)).toBeNull();
  });

  it("shows auth error alert when projects query returns a token refresh failure", () => {
    const onReauthorize = jest.fn();
    mockUseGetJiraProjectsQuery.mockReturnValue({
      ...defaultQueryReturn,
      error: {
        status: 400,
        data: { detail: "Token refresh failed: refresh_token is invalid" },
      },
    });

    render(
      <JiraConfigTab
        connection={mockConnection}
        onReauthorize={onReauthorize}
      />,
    );

    expect(screen.getByText(/jira authorization expired/i)).toBeTruthy();
    expect(screen.getByTestId("reauthorize-jira-btn")).toBeTruthy();
    expect(screen.queryByText(/configure how fides creates/i)).toBeNull();
  });

  it("shows auth error alert on 401 status", () => {
    mockUseGetJiraProjectsQuery.mockReturnValue({
      ...defaultQueryReturn,
      error: { status: 401, data: {} },
    });

    render(<JiraConfigTab connection={mockConnection} />);

    expect(screen.getByText(/jira authorization expired/i)).toBeTruthy();
  });

  it("shows the form (not auth error) for a non-auth 400 error", () => {
    mockUseGetJiraProjectsQuery.mockReturnValue({
      ...defaultQueryReturn,
      error: {
        status: 400,
        data: {
          detail:
            "project_key is required (either as a query param or in connection secrets)",
        },
      },
    });

    render(<JiraConfigTab connection={mockConnection} />);

    expect(screen.getByText(/configure how fides creates/i)).toBeTruthy();
    expect(screen.queryByText(/jira authorization expired/i)).toBeNull();
  });

  it("does not render re-authorize button when onReauthorize is not provided", () => {
    mockUseGetJiraProjectsQuery.mockReturnValue({
      ...defaultQueryReturn,
      error: {
        status: 400,
        data: { detail: "Token refresh failed: refresh_token is invalid" },
      },
    });

    render(<JiraConfigTab connection={mockConnection} />);

    expect(screen.getByText(/jira authorization expired/i)).toBeTruthy();
    expect(screen.queryByTestId("reauthorize-jira-btn")).toBeNull();
  });
});
