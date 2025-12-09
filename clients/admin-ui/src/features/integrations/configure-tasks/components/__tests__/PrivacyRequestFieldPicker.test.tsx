/* eslint-disable import/no-extraneous-dependencies */
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";

import { makeStore } from "~/app/store";

import { PrivacyRequestFieldPicker } from "../PrivacyRequestFieldPicker";

jest.mock(
  "~/features/datastore-connections/connection-manual-tasks.slice",
  () => ({
    useGetPrivacyRequestFieldsQuery: jest.fn(),
  }),
);

jest.mock("~/features/privacy-requests/privacy-requests.slice", () => ({
  useGetPrivacyCenterConfigQuery: jest.fn(),
}));

const mockUseGetPrivacyRequestFieldsQuery =
  require("~/features/datastore-connections/connection-manual-tasks.slice").useGetPrivacyRequestFieldsQuery;
const mockUseGetPrivacyCenterConfigQuery =
  require("~/features/privacy-requests/privacy-requests.slice").useGetPrivacyCenterConfigQuery;

const renderWithProvider = (component: React.ReactElement) => {
  const store = makeStore();
  return render(<Provider store={store}>{component}</Provider>);
};

describe("PrivacyRequestFieldPicker", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const defaultProps = {
    value: undefined,
    onChange: jest.fn(),
    connectionKey: "test_connection",
  };

  it("renders error state", () => {
    mockUseGetPrivacyRequestFieldsQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: { message: "Failed to fetch" },
    });
    mockUseGetPrivacyCenterConfigQuery.mockReturnValue({ data: undefined });

    renderWithProvider(<PrivacyRequestFieldPicker {...defaultProps} />);

    expect(
      screen.getByText(
        "Failed to load privacy request fields. Please try again.",
      ),
    ).toBeInTheDocument();
  });

  it("renders empty state", () => {
    mockUseGetPrivacyRequestFieldsQuery.mockReturnValue({
      data: { privacy_request: {} },
      isLoading: false,
      error: null,
    });
    mockUseGetPrivacyCenterConfigQuery.mockReturnValue({ data: undefined });

    renderWithProvider(<PrivacyRequestFieldPicker {...defaultProps} />);

    expect(
      screen.getByText("No privacy request fields available."),
    ).toBeInTheDocument();
  });

  it("renders select with standard fields", () => {
    mockUseGetPrivacyRequestFieldsQuery.mockReturnValue({
      data: {
        privacy_request: {
          created_at: {
            field_path: "privacy_request.created_at",
            field_type: "string",
            description: "Created at",
            is_convenience_field: false,
          },
        },
      },
      isLoading: false,
      error: null,
    });
    mockUseGetPrivacyCenterConfigQuery.mockReturnValue({ data: undefined });

    renderWithProvider(<PrivacyRequestFieldPicker {...defaultProps} />);

    expect(
      screen.getByTestId("privacy-request-field-select"),
    ).toBeInTheDocument();
  });
});
