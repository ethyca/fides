import { fireEvent, screen, waitFor } from "@testing-library/react";
import React from "react";

import { render } from "~/../__tests__/utils/test-utils";
import SaaSVersionModal from "~/features/connector-templates/SaaSVersionModal";
import {
  useGetConnectorTemplateVersionConfigQuery,
  useGetConnectorTemplateVersionDatasetQuery,
} from "~/features/connector-templates/connector-template.slice";
import { useSaaSVersionModal } from "~/features/connector-templates/hooks/useSaaSVersionModal";
import { useGetDatastoreConnectionByKeyQuery } from "~/features/datastore-connections";

jest.mock("query-string", () => ({
  __esModule: true,
  default: { stringify: jest.fn(), parse: jest.fn() },
}));
jest.mock("react-dnd", () => ({
  useDrag: jest.fn(() => [{}, jest.fn()]),
  useDrop: jest.fn(() => [{}, jest.fn()]),
  DndProvider: ({ children }: { children: React.ReactNode }) => children,
}));
// eslint-disable-next-line global-require
jest.mock(
  "nuqs",
  () => require("../../../../__tests__/utils/nuqs-mock").nuqsMock,
);

// RTK Query hook mocks
jest.mock("~/features/connector-templates/connector-template.slice", () => ({
  useGetConnectorTemplateVersionConfigQuery: jest.fn(),
  useGetConnectorTemplateVersionDatasetQuery: jest.fn(),
}));

jest.mock("~/features/datastore-connections", () => ({
  useGetDatastoreConnectionByKeyQuery: jest.fn(),
  // Store imports datastoreConnectionSlice from this module — provide a minimal stub
  datastoreConnectionSlice: {
    name: "datastoreConnection",
    reducer: (state = {}) => state,
  },
}));

// ── Typed mocks ────────────────────────────────────────────────────────────────

const mockUseConfig = useGetConnectorTemplateVersionConfigQuery as jest.Mock;
const mockUseDataset = useGetConnectorTemplateVersionDatasetQuery as jest.Mock;
const mockUseConnection = useGetDatastoreConnectionByKeyQuery as jest.Mock;

// ── Fixtures ───────────────────────────────────────────────────────────────────

const STRIPE_CONFIG_YAML = `connector_type: stripe\nversion: "0.0.11"\n`;
const STRIPE_DATASET_YAML = `dataset:\n  - name: stripe_dataset\n`;

function setupDefaultMocks() {
  mockUseConfig.mockReturnValue({
    data: STRIPE_CONFIG_YAML,
    isLoading: false,
    isError: false,
  });
  mockUseDataset.mockReturnValue({
    data: STRIPE_DATASET_YAML,
    isLoading: false,
    isError: false,
  });
  mockUseConnection.mockReturnValue({ data: null });
}

// ── SaaSVersionModal (direct usage) ───────────────────────────────────────────

describe("SaaSVersionModal", () => {
  beforeEach(setupDefaultMocks);

  it("shows a loading spinner while config is fetching", () => {
    mockUseConfig.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    render(
      <SaaSVersionModal
        isOpen
        onClose={jest.fn()}
        connectorType="stripe"
        version="0.0.11"
      />,
    );

    // Ant Design Spin renders with class ant-spin
    expect(document.querySelector(".ant-spin")).toBeInTheDocument();
  });

  it("renders the modal title with connector type and version", () => {
    render(
      <SaaSVersionModal
        isOpen
        onClose={jest.fn()}
        connectorType="stripe"
        version="0.0.11"
      />,
    );

    expect(screen.getByText("stripe — v0.0.11")).toBeInTheDocument();
  });

  it("calls the config query with the correct connector type and version", () => {
    render(
      <SaaSVersionModal
        isOpen
        onClose={jest.fn()}
        connectorType="stripe"
        version="0.0.11"
      />,
    );

    expect(mockUseConfig).toHaveBeenCalledWith({
      connectorType: "stripe",
      version: "0.0.11",
    });
  });

  it("calls the dataset query with the correct connector type and version", () => {
    render(
      <SaaSVersionModal
        isOpen
        onClose={jest.fn()}
        connectorType="stripe"
        version="0.0.11"
      />,
    );

    expect(mockUseDataset).toHaveBeenCalledWith({
      connectorType: "stripe",
      version: "0.0.11",
    });
  });

  it("shows 'No dataset available' in the Dataset tab when the dataset endpoint errors", () => {
    mockUseDataset.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });

    render(
      <SaaSVersionModal
        isOpen
        onClose={jest.fn()}
        connectorType="stripe"
        version="0.0.11"
      />,
    );

    // Activate the Dataset tab, then assert the fallback message
    fireEvent.click(screen.getByText("Dataset"));
    expect(
      screen.getByText("No dataset available for this version."),
    ).toBeInTheDocument();
  });

  it("shows an error message when config fails to load", () => {
    mockUseConfig.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });

    render(
      <SaaSVersionModal
        isOpen
        onClose={jest.fn()}
        connectorType="stripe"
        version="0.0.11"
      />,
    );

    expect(
      screen.getByText("Could not load version config."),
    ).toBeInTheDocument();
  });

  it("calls onClose when the Close button is clicked", () => {
    const onClose = jest.fn();

    render(
      <SaaSVersionModal
        isOpen
        onClose={onClose}
        connectorType="stripe"
        version="0.0.11"
      />,
    );

    fireEvent.click(screen.getByTestId("version-modal-close-btn"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("does not render when isOpen is false", () => {
    render(
      <SaaSVersionModal
        isOpen={false}
        onClose={jest.fn()}
        connectorType="stripe"
        version="0.0.11"
      />,
    );

    expect(screen.queryByText("stripe — v0.0.11")).not.toBeInTheDocument();
  });
});

// ── useSaaSVersionModal hook ───────────────────────────────────────────────────

const HookConsumer = ({
  connectionKey,
  version,
}: {
  connectionKey: string;
  version: string;
}) => {
  const { openVersionModal, modal } = useSaaSVersionModal();
  return (
    <>
      {modal}
      <button
        type="button"
        data-testid="trigger"
        onClick={() => openVersionModal(connectionKey, version)}
      >
        Open
      </button>
    </>
  );
};

describe("useSaaSVersionModal", () => {
  beforeEach(setupDefaultMocks);

  it("opens the modal once the connection resolves a connector type", async () => {
    mockUseConnection.mockReturnValue({
      data: { saas_config: { type: "stripe" } },
    });

    render(<HookConsumer connectionKey="stripe_conn" version="0.0.11" />);

    fireEvent.click(screen.getByTestId("trigger"));

    await waitFor(() => {
      expect(screen.getByText("stripe — v0.0.11")).toBeInTheDocument();
    });
  });

  it("does not open if the connection has no saas_config type", async () => {
    mockUseConnection.mockReturnValue({ data: { saas_config: null } });

    render(<HookConsumer connectionKey="plain_conn" version="0.0.11" />);

    fireEvent.click(screen.getByTestId("trigger"));

    await waitFor(() => {
      expect(screen.queryByText(/— v0\.0\.11/)).not.toBeInTheDocument();
    });
  });
});
