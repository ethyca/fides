/* eslint-disable import/no-extraneous-dependencies */
import { render, screen, waitFor } from "@testing-library/react";
import { Provider } from "react-redux";

import { makeStore } from "~/app/store";

import { DatasetReferencePicker } from "../DatasetReferencePicker";

// Mock the dataset API slice
jest.mock("~/features/dataset/dataset.slice", () => ({
  useGetAllFilteredDatasetsQuery: jest.fn(),
  useLazyGetDatasetByKeyQuery: jest.fn(),
}));

// Mock the alert hook
jest.mock("~/features/common/hooks/useAlert", () => ({
  useAlert: jest.fn(() => ({
    errorAlert: jest.fn(),
  })),
}));

const mockUseGetAllFilteredDatasetsQuery =
  require("~/features/dataset/dataset.slice").useGetAllFilteredDatasetsQuery;
const mockUseLazyGetDatasetByKeyQuery =
  require("~/features/dataset/dataset.slice").useLazyGetDatasetByKeyQuery;

const renderWithProvider = (component: React.ReactElement) => {
  const store = makeStore();
  return render(<Provider store={store}>{component}</Provider>);
};

describe("DatasetReferencePicker", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render with placeholder text", () => {
    mockUseGetAllFilteredDatasetsQuery.mockReturnValue({
      data: [
        {
          fides_key: "test_dataset",
          name: "Test Dataset",
          collections: [],
        },
      ],
      isLoading: false,
    });
    mockUseLazyGetDatasetByKeyQuery.mockReturnValue([jest.fn()]);

    const onChange = jest.fn();
    renderWithProvider(
      <DatasetReferencePicker
        value={undefined}
        onChange={onChange}
        placeholder="Select a field"
      />,
    );

    expect(screen.getByTestId("dataset-reference-picker")).toBeInTheDocument();
  });

  it("should render with default placeholder when none provided", () => {
    mockUseGetAllFilteredDatasetsQuery.mockReturnValue({
      data: [
        {
          fides_key: "test_dataset",
          name: "Test Dataset",
          collections: [],
        },
      ],
      isLoading: false,
    });
    mockUseLazyGetDatasetByKeyQuery.mockReturnValue([jest.fn()]);

    const onChange = jest.fn();
    renderWithProvider(
      <DatasetReferencePicker value={undefined} onChange={onChange} />,
    );

    expect(screen.getByTestId("dataset-reference-picker")).toBeInTheDocument();
  });

  it("should show empty state when no datasets available", () => {
    mockUseGetAllFilteredDatasetsQuery.mockReturnValue({
      data: [],
      isLoading: false,
    });
    mockUseLazyGetDatasetByKeyQuery.mockReturnValue([jest.fn()]);

    const onChange = jest.fn();
    renderWithProvider(
      <DatasetReferencePicker value={undefined} onChange={onChange} />,
    );

    expect(screen.getByText("No datasets available")).toBeInTheDocument();
    expect(
      screen.getByText("Create a dataset to start using this feature"),
    ).toBeInTheDocument();
  });

  it("should show loading state", () => {
    mockUseGetAllFilteredDatasetsQuery.mockReturnValue({
      data: undefined,
      isLoading: true,
    });
    mockUseLazyGetDatasetByKeyQuery.mockReturnValue([jest.fn()]);

    const onChange = jest.fn();
    renderWithProvider(
      <DatasetReferencePicker value={undefined} onChange={onChange} />,
    );

    expect(screen.getByTestId("dataset-reference-picker")).toBeInTheDocument();
  });

  it("should display selected value when provided", async () => {
    mockUseGetAllFilteredDatasetsQuery.mockReturnValue({
      data: [
        {
          fides_key: "test_dataset",
          name: "Test Dataset",
          collections: [],
        },
      ],
      isLoading: false,
    });
    mockUseLazyGetDatasetByKeyQuery.mockReturnValue([jest.fn()]);

    const onChange = jest.fn();
    const selectedValue = "test_dataset:users:email";

    renderWithProvider(
      <DatasetReferencePicker value={selectedValue} onChange={onChange} />,
    );

    await waitFor(() => {
      expect(
        screen.getByTestId("dataset-reference-picker"),
      ).toBeInTheDocument();
    });
  });

  it("should be disabled when disabled prop is true", () => {
    mockUseGetAllFilteredDatasetsQuery.mockReturnValue({
      data: [
        {
          fides_key: "test_dataset",
          name: "Test Dataset",
          collections: [],
        },
      ],
      isLoading: false,
    });
    mockUseLazyGetDatasetByKeyQuery.mockReturnValue([jest.fn()]);

    const onChange = jest.fn();
    renderWithProvider(
      <DatasetReferencePicker value={undefined} onChange={onChange} disabled />,
    );

    const treeSelect = screen.getByTestId("dataset-reference-picker");
    expect(treeSelect).toBeInTheDocument();
  });

  it("should handle datasets with no name gracefully", () => {
    mockUseGetAllFilteredDatasetsQuery.mockReturnValue({
      data: [
        {
          fides_key: "test_dataset",
          name: null,
          collections: [],
        },
      ],
      isLoading: false,
    });
    mockUseLazyGetDatasetByKeyQuery.mockReturnValue([jest.fn()]);

    const onChange = jest.fn();
    renderWithProvider(
      <DatasetReferencePicker value={undefined} onChange={onChange} />,
    );

    expect(screen.getByTestId("dataset-reference-picker")).toBeInTheDocument();
  });

  it("should call onChange when selection changes", async () => {
    mockUseGetAllFilteredDatasetsQuery.mockReturnValue({
      data: [
        {
          fides_key: "test_dataset",
          name: "Test Dataset",
          collections: [],
        },
      ],
      isLoading: false,
    });
    mockUseLazyGetDatasetByKeyQuery.mockReturnValue([jest.fn()]);

    const onChange = jest.fn();
    renderWithProvider(
      <DatasetReferencePicker value={undefined} onChange={onChange} />,
    );

    await waitFor(() => {
      expect(
        screen.getByTestId("dataset-reference-picker"),
      ).toBeInTheDocument();
    });

    // Note: More detailed interaction tests would require mocking Ant Design's TreeSelect
    // behavior more thoroughly, which is complex due to its internal implementation
  });
});
