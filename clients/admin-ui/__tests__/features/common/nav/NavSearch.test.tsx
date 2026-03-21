import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { NavGroup } from "~/features/common/nav/nav-config";
import { FlatNavItem } from "~/features/common/nav/useNavSearchItems";

// Mock fidesui to avoid jsdom incompatibilities with Ant Design components.
// NavSearch imports: AutoComplete, Icons, Input, InputRef, Modal
jest.mock("fidesui", () => {
  // eslint-disable-next-line global-require
  const MockReact = require("react");
  return {
    __esModule: true,
    AutoComplete: (props: any) => {
      (global as any).mockAutoCompleteProps = props;
      const { options, onSelect, open, children, value, onSearch } = props;
      return MockReact.createElement(
        "div",
        { "data-testid": "mock-autocomplete", "data-open": String(open) },
        MockReact.cloneElement(children, {
          value,
          onChange: (e: any) => onSearch?.(e.target.value),
        }),
        open
          ? MockReact.createElement(
              "ul",
              { "data-testid": "mock-autocomplete-dropdown" },
              options?.map((group: any, gi: number) =>
                MockReact.createElement(
                  "li",
                  { key: gi, "data-testid": "option-group" },
                  MockReact.createElement(
                    "span",
                    { "data-testid": "group-label" },
                    group.label,
                  ),
                  MockReact.createElement(
                    "ul",
                    null,
                    group.options?.map((opt: any) =>
                      MockReact.createElement(
                        "li",
                        { key: opt.value },
                        MockReact.createElement(
                          "button",
                          {
                            type: "button",
                            "data-testid": `option-${opt.value}`,
                            onClick: () => onSelect?.(opt.value),
                          },
                          opt.label,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            )
          : null,
      );
    },
    Input: MockReact.forwardRef((props: any, ref: any) => {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { prefix, suffix, allowClear, autoFocus, ...rest } = props;
      return MockReact.createElement("input", { ...rest, ref });
    }),
    Modal: ({ open: modalOpen, children, onCancel, destroyOnClose }: any) => {
      if (!modalOpen) {
        if (destroyOnClose) {
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

// Mock palette to avoid SCSS import issues
jest.mock("fidesui/src/palette/palette.module.scss", () => ({
  FIDESUI_CORINTH: "#fafafa",
  FIDESUI_NEUTRAL_400: "#a8aaad",
}));

// Mock useNavSearchItems to return static + dynamic items without Redux
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

// Must import NavSearch after mocks are set up
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
      {
        title: "Hidden route",
        path: "/hidden",
        hidden: true,
        children: [],
      },
    ],
  },
  {
    title: "Settings",
    icon: "icon" as unknown as React.ReactNode,
    children: [
      {
        title: "Privacy requests",
        path: "/settings/privacy-requests",
        children: [],
        tabs: [
          {
            title: "Redaction patterns",
            path: "/settings/privacy-requests",
          },
          {
            title: "Duplicate detection",
            path: "/settings/privacy-requests",
          },
        ],
      },
    ],
  },
];

const getAutoCompleteProps = (): Record<string, any> =>
  (global as any).mockAutoCompleteProps ?? {};

const getOptionValues = (): string[] => {
  const options = getAutoCompleteProps().options ?? [];
  return options.flatMap((g: any) => g.options.map((o: any) => o.value));
};

const getGroupLabels = (): string[] => {
  const options = getAutoCompleteProps().options ?? [];
  return options.map((g: any) => g.label.props.children as string);
};

beforeEach(() => {
  jest.clearAllMocks();
  (global as any).mockAutoCompleteProps = {};
});

afterEach(() => {
  mockDynamicItems.length = 0;
});

describe("NavSearch", () => {
  describe("expanded mode", () => {
    it("renders the search input", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      expect(screen.getByTestId("nav-search-input")).toBeInTheDocument();
    });

    it("does not render the collapsed toggle button", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      expect(screen.queryByTestId("nav-search-toggle")).not.toBeInTheDocument();
    });

    it("sets defaultActiveFirstOption for Enter key selection", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      fireEvent.focus(screen.getByTestId("nav-search-input"));

      expect(getAutoCompleteProps().defaultActiveFirstOption).toBe(true);
    });
  });

  describe("filtering", () => {
    it("excludes hidden routes from the options", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      fireEvent.focus(screen.getByTestId("nav-search-input"));

      expect(getOptionValues()).not.toContain("/hidden");
    });

    it("includes all visible routes when no search query", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      fireEvent.focus(screen.getByTestId("nav-search-input"));

      const values = getOptionValues();
      expect(values).toContain("/");
      expect(values).toContain("/systems");
      expect(values).toContain("/dataset");
      expect(values).toContain("/privacy-requests");
    });

    it("filters options when typing a search query", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      const input = screen.getByTestId("nav-search-input");

      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: "System" } });

      const values = getOptionValues();
      expect(values).toContain("/systems");
      expect(values).not.toContain("/dataset");
    });

    it("is case-insensitive", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      const input = screen.getByTestId("nav-search-input");

      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: "system" } });

      expect(getOptionValues()).toContain("/systems");
    });

    it("returns no options when nothing matches", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      const input = screen.getByTestId("nav-search-input");

      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: "zzzznonexistent" } });

      expect(getOptionValues()).toHaveLength(0);
    });

    it("groups options by nav group", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      fireEvent.focus(screen.getByTestId("nav-search-input"));

      const labels = getGroupLabels();
      expect(labels).toContain("Overview");
      expect(labels).toContain("Data inventory");
      expect(labels).toContain("Privacy requests");
    });

    it("only shows matching groups when filtering", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      const input = screen.getByTestId("nav-search-input");

      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: "Home" } });

      const labels = getGroupLabels();
      expect(labels).toContain("Overview");
      expect(labels).not.toContain("Data inventory");
    });
  });

  describe("keyboard shortcuts", () => {
    it("opens search on Cmd+K", async () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);

      fireEvent.keyDown(document, { key: "k", metaKey: true });

      await waitFor(() => {
        expect(getAutoCompleteProps().open).toBe(true);
      });
    });

    it("opens search on Ctrl+K", async () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);

      fireEvent.keyDown(document, { key: "k", ctrlKey: true });

      await waitFor(() => {
        expect(getAutoCompleteProps().open).toBe(true);
      });
    });

    it("does not open on K without modifier key", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);

      fireEvent.keyDown(document, { key: "k" });

      expect(getAutoCompleteProps().open).toBeFalsy();
    });
  });

  describe("navigation", () => {
    it("navigates to the selected route", async () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);

      fireEvent.focus(screen.getByTestId("nav-search-input"));
      await waitFor(() => {
        expect(getAutoCompleteProps().open).toBe(true);
      });

      fireEvent.click(screen.getByTestId("option-/systems"));

      expect(mockPush).toHaveBeenCalledWith("/systems");
    });

    it("clears the search value after selection", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      const input = screen.getByTestId("nav-search-input");

      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: "System" } });

      fireEvent.click(screen.getByTestId("option-/systems"));

      expect(getAutoCompleteProps().value).toBe("");
    });

    it("closes the dropdown after selection", async () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);

      fireEvent.focus(screen.getByTestId("nav-search-input"));
      await waitFor(() => {
        expect(getAutoCompleteProps().open).toBe(true);
      });

      fireEvent.click(screen.getByTestId("option-/systems"));

      expect(getAutoCompleteProps().open).toBe(false);
    });
  });

  describe("tabs", () => {
    it("includes tab items in search results", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      const input = screen.getByTestId("nav-search-input");

      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: "Manual" } });

      const values = getOptionValues();
      expect(values).toContain(
        "/privacy-requests?tab=manual-tasks::Manual tasks",
      );
    });

    it("navigates to tab path on selection", async () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      const input = screen.getByTestId("nav-search-input");

      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: "Manual" } });

      await waitFor(() => {
        expect(getAutoCompleteProps().open).toBe(true);
      });

      fireEvent.click(
        screen.getByTestId(
          "option-/privacy-requests?tab=manual-tasks::Manual tasks",
        ),
      );

      expect(mockPush).toHaveBeenCalledWith(
        "/privacy-requests?tab=manual-tasks",
      );
    });

    it("includes both parent page and its tabs in results", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      const input = screen.getByTestId("nav-search-input");

      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: "Request" } });

      const values = getOptionValues();
      expect(values).toContain("/privacy-requests");
      expect(values).toContain("/privacy-requests?tab=request::Requests");
    });
  });

  describe("duplicate paths", () => {
    it("renders both items when two tabs share the same path", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      const input = screen.getByTestId("nav-search-input");

      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: "tion" } });

      const values = getOptionValues();
      expect(values).toContain(
        "/settings/privacy-requests::Redaction patterns",
      );
      expect(values).toContain(
        "/settings/privacy-requests::Duplicate detection",
      );
    });

    it("navigates correctly when selecting a duplicate-path item", async () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      const input = screen.getByTestId("nav-search-input");

      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: "Redaction" } });

      await waitFor(() => {
        expect(getAutoCompleteProps().open).toBe(true);
      });

      fireEvent.click(
        screen.getByTestId(
          "option-/settings/privacy-requests::Redaction patterns",
        ),
      );

      expect(mockPush).toHaveBeenCalledWith("/settings/privacy-requests");
    });
  });

  describe("sub-items visibility", () => {
    it("does not show tabs when there is no search query", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      fireEvent.focus(screen.getByTestId("nav-search-input"));

      const values = getOptionValues();
      expect(values).toContain("/privacy-requests");
      const tabRequest = "/privacy-requests?tab=request::Requests";
      const tabManual = "/privacy-requests?tab=manual-tasks::Manual tasks";
      expect(values).not.toContain(tabRequest);
      expect(values).not.toContain(tabManual);
    });

    it("shows tabs only when the search query matches them", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      const input = screen.getByTestId("nav-search-input");

      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: "Manual" } });

      const values = getOptionValues();
      const tabManual = "/privacy-requests?tab=manual-tasks::Manual tasks";
      const tabRequest = "/privacy-requests?tab=request::Requests";
      expect(values).toContain(tabManual);
      expect(values).not.toContain(tabRequest);
    });
  });

  describe("dynamic items", () => {
    it("includes dynamic taxonomy items when search matches", () => {
      mockDynamicItems.push({
        title: "Marketing",
        path: "/taxonomy/data_use",
        groupTitle: "Core configuration",
        parentTitle: "Taxonomy",
      });

      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      const input = screen.getByTestId("nav-search-input");

      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: "Marketing" } });

      expect(getOptionValues()).toContain("/taxonomy/data_use::Marketing");
    });

    it("includes dynamic integration items when search matches", () => {
      mockDynamicItems.push({
        title: "Stripe Production",
        path: "/integrations/stripe-prod",
        groupTitle: "Core configuration",
        parentTitle: "Integrations",
      });

      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      const input = screen.getByTestId("nav-search-input");

      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: "Stripe" } });

      expect(getOptionValues()).toContain(
        "/integrations/stripe-prod::Stripe Production",
      );
    });

    it("does not show dynamic items when there is no search query", () => {
      mockDynamicItems.push({
        title: "Marketing",
        path: "/taxonomy/data_use",
        groupTitle: "Core configuration",
        parentTitle: "Taxonomy",
      });

      const NavSearch = getNavSearch();
      render(<NavSearch groups={MOCK_GROUPS} />);
      fireEvent.focus(screen.getByTestId("nav-search-input"));

      expect(getOptionValues()).not.toContain("/taxonomy/data_use::Marketing");
    });
  });

  describe("with empty groups", () => {
    it("renders with no options when groups are empty", () => {
      const NavSearch = getNavSearch();
      render(<NavSearch groups={[]} />);
      fireEvent.focus(screen.getByTestId("nav-search-input"));

      expect(getOptionValues()).toHaveLength(0);
    });
  });
});
