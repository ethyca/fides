import { render, screen } from "@testing-library/react";

import OAuthClientsList from "./OAuthClientsTable";

// --- Module mocks ---

const mockUseHasPermission = jest.fn();
jest.mock("~/features/common/Restrict", () => ({
  useHasPermission: () => mockUseHasPermission(),
}));

const mockUseListOAuthClientsQuery = jest.fn();
jest.mock("./oauth-clients.slice", () => ({
  useListOAuthClientsQuery: () => mockUseListOAuthClientsQuery(),
}));

// LinkCell uses NextLink which doesn't work in jsdom (NodeList.includes bug)
jest.mock("~/features/common/table/cells/LinkCell", () => ({
  LinkCell: ({ href, children }: any) =>
    href ? <a href={href}>{children}</a> : <span>{children}</span>,
}));

// Tooltip mock: real Tooltip only renders content in a portal on hover,
// so we use a lightweight stand-in that exposes the title as a DOM attribute
// for static assertions.
const MockTooltip = ({ title, children }: any) => (
  <span data-tooltip={title}>{children}</span>
);
MockTooltip.displayName = "MockTooltip";

jest.mock(
  "fidesui",
  () =>
    new Proxy(jest.requireActual("fidesui"), {
      get(target, prop) {
        if (prop === "Tooltip") {
          return MockTooltip;
        }
        return target[prop as keyof typeof target];
      },
    }),
);

// --- Helpers ---

const makeClient = (overrides = {}) => ({
  client_id: "abc123",
  name: "My Client",
  description: "A test client",
  scopes: ["client:create", "client:read"],
  ...overrides,
});

const renderList = () => render(<OAuthClientsList />);

// --- Tests ---

describe("OAuthClientsList", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: jest.fn() },
      configurable: true,
    });
    mockUseHasPermission.mockReturnValue(true);
    mockUseListOAuthClientsQuery.mockReturnValue({
      data: { items: [makeClient()], total: 1, page: 1, size: 25 },
      isLoading: false,
    });
  });

  describe("list item rendering", () => {
    it("renders the client name", () => {
      renderList();
      expect(screen.getByText("My Client")).toBeInTheDocument();
    });

    it("renders the client ID in monospace", () => {
      renderList();
      expect(screen.getByText("abc123")).toBeInTheDocument();
    });

    it("renders the scope count tag", () => {
      renderList();
      expect(screen.getByText("2 scopes")).toBeInTheDocument();
    });

    it("renders the description when present", () => {
      renderList();
      expect(screen.getByText("A test client")).toBeInTheDocument();
    });

    it("does not render a description section when absent", () => {
      mockUseListOAuthClientsQuery.mockReturnValue({
        data: { items: [makeClient({ description: null })], total: 1 },
        isLoading: false,
      });
      renderList();
      expect(screen.queryByText("A test client")).not.toBeInTheDocument();
    });

    it("renders a copy button for the client ID", () => {
      renderList();
      expect(screen.getByTestId("clipboard-btn")).toBeInTheDocument();
    });

    it("shows 'Unnamed' when client has no name", () => {
      mockUseListOAuthClientsQuery.mockReturnValue({
        data: { items: [makeClient({ name: null })], total: 1 },
        isLoading: false,
      });
      renderList();
      expect(screen.getByText("Unnamed")).toBeInTheDocument();
    });
  });

  describe("empty state", () => {
    it("renders empty state text when there are no clients", () => {
      mockUseListOAuthClientsQuery.mockReturnValue({
        data: { items: [], total: 0 },
        isLoading: false,
      });
      renderList();
      expect(screen.getByText(/No API clients yet/)).toBeInTheDocument();
    });
  });

  describe("loading state", () => {
    it("renders without crashing while loading", () => {
      mockUseListOAuthClientsQuery.mockReturnValue({
        data: undefined,
        isLoading: true,
      });
      expect(() => renderList()).not.toThrow();
    });
  });

  describe("client name link — with CLIENT_UPDATE permission", () => {
    it("renders the name as a link to the detail page", () => {
      mockUseHasPermission.mockReturnValue(true);
      renderList();
      const link = screen.getByText("My Client").closest("a");
      expect(link).toHaveAttribute("href", "/api-clients/abc123");
    });

    it("does not show a permission tooltip", () => {
      mockUseHasPermission.mockReturnValue(true);
      renderList();
      const tooltip = screen.getByText("My Client").closest("[data-tooltip]");
      expect(tooltip?.getAttribute("data-tooltip")).toBeFalsy();
    });
  });

  describe("client name — without CLIENT_UPDATE permission", () => {
    beforeEach(() => mockUseHasPermission.mockReturnValue(false));

    it("renders the name as plain text (no link)", () => {
      renderList();
      expect(screen.getByText("My Client").closest("a")).toBeNull();
    });

    it("shows a tooltip explaining the permission requirement", () => {
      renderList();
      const tooltip = screen.getByText("My Client").closest("[data-tooltip]");
      expect(tooltip?.getAttribute("data-tooltip")).toMatch(/permission/i);
    });
  });

  describe("pagination", () => {
    it("always renders the pagination component", () => {
      renderList();
      expect(screen.getByText(/Total 1 items/)).toBeInTheDocument();
    });

    it("shows the total item count", () => {
      mockUseListOAuthClientsQuery.mockReturnValue({
        data: { items: [makeClient()], total: 42 },
        isLoading: false,
      });
      renderList();
      expect(screen.getByText(/Total 42 items/)).toBeInTheDocument();
    });
  });
});
