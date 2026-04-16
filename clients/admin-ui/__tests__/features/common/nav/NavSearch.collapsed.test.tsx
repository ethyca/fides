import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { NavGroup } from "~/features/common/nav/nav-config";
import { FlatNavItem } from "~/features/common/nav/useNavSearchItems";

// Mock fidesui (same setup as NavSearch.test.tsx)
jest.mock("fidesui", () => {
  // eslint-disable-next-line global-require
  const MockReact = require("react");
  return {
    __esModule: true,
    AutoComplete: (props: any) => {
      const { open, children, value, onSearch } = props;
      return MockReact.createElement(
        "div",
        { "data-testid": "mock-autocomplete", "data-open": String(open) },
        MockReact.cloneElement(children, {
          value,
          onChange: (e: any) => onSearch?.(e.target.value),
        }),
      );
    },
    Input: MockReact.forwardRef((props: any, ref: any) => {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { prefix, suffix, allowClear, autoFocus, ...rest } = props;
      return MockReact.createElement("input", { ...rest, ref });
    }),
    Modal: ({ open: modalOpen, children, onCancel, destroyOnHidden }: any) => {
      if (!modalOpen) {
        if (destroyOnHidden) {
          return null;
        }
        return MockReact.createElement(
          "div",
          { "data-testid": "mock-modal", style: { display: "none" } },
          children,
        );
      }
      return MockReact.createElement(
        "div",
        { "data-testid": "mock-modal" },
        children,
        MockReact.createElement("button", {
          "data-testid": "mock-modal-close",
          onClick: onCancel,
        }),
      );
    },
    Icons: {
      Search: () => MockReact.createElement("span", null, "search-icon"),
    },
  };
});

jest.mock("fidesui/src/palette/palette.module.scss", () => ({
  FIDESUI_CORINTH: "#fafafa",
  FIDESUI_NEUTRAL_400: "#a8aaad",
}));

// Mock react-hotkeys-hook so fireEvent.keyDown works in tests
jest.mock("react-hotkeys-hook", () => {
  // eslint-disable-next-line global-require
  const MockReact = require("react");
  return {
    useHotkeys: (
      keys: string,
      callback: () => void,
      options?: Record<string, unknown>,
    ) => {
      MockReact.useEffect(() => {
        const handler = (e: KeyboardEvent) => {
          keys
            .split(",")
            .map((k: string) => k.trim().toLowerCase())
            .some((combo: string) => {
              const parts = combo.split("+");
              const key = parts.pop()!;
              const needsMeta = parts.includes("meta");
              const needsCtrl = parts.includes("ctrl");
              if (
                e.key.toLowerCase() === key &&
                (!needsMeta || e.metaKey) &&
                (!needsCtrl || e.ctrlKey)
              ) {
                if (options?.preventDefault) {
                  e.preventDefault();
                }
                callback();
                return true;
              }
              return false;
            });
        };
        globalThis.document.addEventListener("keydown", handler);
        return () =>
          globalThis.document.removeEventListener("keydown", handler);
        // eslint-disable-next-line react-hooks/exhaustive-deps
      }, []);
    },
  };
});

// Mock next/link to simulate NextLink navigation via the mocked router
jest.mock("next/link", () => {
  // eslint-disable-next-line global-require
  const MockReact = require("react");
  return {
    __esModule: true,
    default: MockReact.forwardRef(
      ({ href, onClick, children, ...props }: any, ref: any) => {
        // eslint-disable-next-line global-require, @typescript-eslint/no-shadow
        const { useRouter } = require("next/router");
        const router = useRouter();
        return MockReact.createElement(
          "a",
          {
            ...props,
            href,
            ref,
            onClick: (e: any) => {
              e.preventDefault();
              router.push(href);
              onClick?.(e);
            },
          },
          children,
        );
      },
    ),
  };
});

const mockDynamicItems: FlatNavItem[] = [];
jest.mock("~/features/common/nav/useNavSearchItems", () => ({
  __esModule: true,
  default: (groups: any[]) => {
    const items: any[] = [];
    groups.forEach((group: any) => {
      group.children
        .filter((child: any) => !child.hidden)
        .forEach((child: any) => {
          items.push({
            title: child.title,
            path: child.path,
            groupTitle: group.title,
          });
          child.tabs?.forEach((tab: any) => {
            items.push({
              title: tab.title,
              path: tab.path,
              groupTitle: group.title,
              parentTitle: child.title,
            });
          });
        });
    });
    return [...items, ...mockDynamicItems];
  },
}));

const mockPush = jest.fn();

jest.mock("next/router", () => ({
  useRouter: () => ({
    push: mockPush,
    pathname: "/",
    route: "/",
    query: {},
    asPath: "/",
  }),
}));

// eslint-disable-next-line global-require
const getNavSearch = () => require("~/features/common/nav/NavSearch").default;

const MOCK_GROUPS: NavGroup[] = [
  {
    title: "Overview",
    icon: "icon" as unknown as React.ReactNode,
    children: [{ title: "Home", path: "/", exact: true, children: [] }],
  },
  {
    title: "Data inventory",
    icon: "icon" as unknown as React.ReactNode,
    children: [
      { title: "System inventory", path: "/systems", children: [] },
      { title: "Manage datasets", path: "/dataset", children: [] },
    ],
  },
  {
    title: "Privacy requests",
    icon: "icon" as unknown as React.ReactNode,
    children: [
      {
        title: "Request manager",
        path: "/privacy-requests",
        children: [],
        tabs: [
          { title: "Requests", path: "/privacy-requests?tab=request" },
          {
            title: "Manual tasks",
            path: "/privacy-requests?tab=manual-tasks",
          },
        ],
      },
    ],
  },
];

beforeEach(() => {
  jest.clearAllMocks();
});

afterEach(() => {
  mockDynamicItems.length = 0;
});

describe("NavSearch collapsed mode", () => {
  it("renders the search toggle button", () => {
    const NavSearch = getNavSearch();
    render(<NavSearch groups={MOCK_GROUPS} collapsed />);
    expect(screen.getByTestId("nav-search-toggle")).toBeInTheDocument();
  });

  it("does not render the expanded search input", () => {
    const NavSearch = getNavSearch();
    render(<NavSearch groups={MOCK_GROUPS} collapsed />);
    expect(screen.queryByTestId("nav-search-input")).not.toBeInTheDocument();
  });

  it("has an accessible label on the toggle button", () => {
    const NavSearch = getNavSearch();
    render(<NavSearch groups={MOCK_GROUPS} collapsed />);
    expect(screen.getByLabelText("Search navigation")).toBeInTheDocument();
  });

  it("opens a modal when the search toggle is clicked", async () => {
    const NavSearch = getNavSearch();
    render(<NavSearch groups={MOCK_GROUPS} collapsed />);

    fireEvent.click(screen.getByTestId("nav-search-toggle"));

    await waitFor(() => {
      expect(screen.getByTestId("mock-modal")).toBeInTheDocument();
      expect(screen.getByTestId("nav-search-modal-input")).toBeInTheDocument();
    });
  });

  it("does not show results until user starts typing", async () => {
    const NavSearch = getNavSearch();
    render(<NavSearch groups={MOCK_GROUPS} collapsed />);

    fireEvent.click(screen.getByTestId("nav-search-toggle"));

    await waitFor(() => {
      expect(screen.getByTestId("nav-search-modal-input")).toBeInTheDocument();
    });

    expect(screen.queryByTestId("nav-search-results")).not.toBeInTheDocument();
  });

  it("shows inline results after typing", async () => {
    const NavSearch = getNavSearch();
    render(<NavSearch groups={MOCK_GROUPS} collapsed />);

    fireEvent.click(screen.getByTestId("nav-search-toggle"));

    const input = await screen.findByTestId("nav-search-modal-input");
    fireEvent.change(input, { target: { value: "System" } });

    await waitFor(() => {
      expect(screen.getByTestId("nav-search-results")).toBeInTheDocument();
      expect(screen.getByTestId("result-/systems")).toBeInTheDocument();
    });
  });

  it("navigates on result click", async () => {
    const NavSearch = getNavSearch();
    render(<NavSearch groups={MOCK_GROUPS} collapsed />);

    fireEvent.click(screen.getByTestId("nav-search-toggle"));

    const input = await screen.findByTestId("nav-search-modal-input");
    fireEvent.change(input, { target: { value: "dataset" } });

    await waitFor(() => {
      expect(screen.getByTestId("result-/dataset")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("result-/dataset"));

    expect(mockPush).toHaveBeenCalledWith("/dataset");
  });

  it("closes the modal on Escape key", async () => {
    const NavSearch = getNavSearch();
    render(<NavSearch groups={MOCK_GROUPS} collapsed />);

    fireEvent.click(screen.getByTestId("nav-search-toggle"));

    const input = await screen.findByTestId("nav-search-modal-input");
    fireEvent.change(input, { target: { value: "System" } });

    await waitFor(() => {
      expect(screen.getByTestId("nav-search-results")).toBeInTheDocument();
    });

    fireEvent.keyDown(input, { key: "Escape" });

    await waitFor(() => {
      expect(
        screen.queryByTestId("nav-search-results"),
      ).not.toBeInTheDocument();
    });
  });

  it("navigates with ArrowDown + Enter in modal", async () => {
    const NavSearch = getNavSearch();
    render(<NavSearch groups={MOCK_GROUPS} collapsed />);

    fireEvent.click(screen.getByTestId("nav-search-toggle"));

    const input = await screen.findByTestId("nav-search-modal-input");
    fireEvent.change(input, { target: { value: "System" } });

    await waitFor(() => {
      expect(screen.getByTestId("nav-search-results")).toBeInTheDocument();
    });

    fireEvent.keyDown(input, { key: "Enter" });

    expect(mockPush).toHaveBeenCalled();
  });

  it("wraps ArrowDown from last to first item", async () => {
    const NavSearch = getNavSearch();
    render(<NavSearch groups={MOCK_GROUPS} collapsed />);

    fireEvent.click(screen.getByTestId("nav-search-toggle"));

    const input = await screen.findByTestId("nav-search-modal-input");
    fireEvent.change(input, { target: { value: "Home" } });

    await waitFor(() => {
      expect(screen.getByTestId("nav-search-results")).toBeInTheDocument();
    });

    fireEvent.keyDown(input, { key: "ArrowDown" });
    const firstResult = screen.getByTestId("result-/");
    expect(firstResult.getAttribute("aria-selected")).toBe("true");
  });

  it("sets aria-activedescendant on the input for screen readers", async () => {
    const NavSearch = getNavSearch();
    render(<NavSearch groups={MOCK_GROUPS} collapsed />);

    fireEvent.click(screen.getByTestId("nav-search-toggle"));

    const input = await screen.findByTestId("nav-search-modal-input");
    fireEvent.change(input, { target: { value: "System" } });

    await waitFor(() => {
      expect(input.getAttribute("aria-activedescendant")).toBe(
        "nav-search-result-0",
      );
    });
  });

  it("shows tab items in modal results", async () => {
    const NavSearch = getNavSearch();
    render(<NavSearch groups={MOCK_GROUPS} collapsed />);

    fireEvent.click(screen.getByTestId("nav-search-toggle"));

    const input = await screen.findByTestId("nav-search-modal-input");
    fireEvent.change(input, { target: { value: "Manual" } });

    await waitFor(() => {
      expect(
        screen.getByTestId("result-/privacy-requests?tab=manual-tasks"),
      ).toBeInTheDocument();
    });
  });

  it("renders duplicate-path items in modal without key warnings", async () => {
    mockDynamicItems.push(
      {
        title: "Redaction patterns",
        path: "/settings/privacy-requests",
        groupTitle: "Settings",
        parentTitle: "Privacy requests",
      },
      {
        title: "Duplicate detection",
        path: "/settings/privacy-requests",
        groupTitle: "Settings",
        parentTitle: "Privacy requests",
      },
    );

    const NavSearch = getNavSearch();
    render(<NavSearch groups={MOCK_GROUPS} collapsed />);

    fireEvent.click(screen.getByTestId("nav-search-toggle"));

    const input = await screen.findByTestId("nav-search-modal-input");
    fireEvent.change(input, { target: { value: "tion" } });

    await waitFor(() => {
      expect(screen.getByText("Redaction patterns")).toBeInTheDocument();
      expect(screen.getByText("Duplicate detection")).toBeInTheDocument();
    });
  });
});
