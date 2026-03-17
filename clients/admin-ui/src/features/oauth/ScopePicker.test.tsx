import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ScopeRegistryEnum } from "~/types/api";

import ScopePicker from "./ScopePicker";

// Render Checkbox as a native checkbox so we can assert on .checked and .indeterminate
const MockCheckbox = ({
  checked,
  indeterminate,
  onChange,
  children,
  "data-testid": testId,
  ...props
}: any) => (
  <label>
    <input
      type="checkbox"
      checked={checked ?? false}
      ref={(el) => {
        if (el) {
          // eslint-disable-next-line no-param-reassign
          el.indeterminate = !!indeterminate;
        }
      }}
      onChange={onChange}
      data-testid={testId}
      {...props}
    />
    {children}
  </label>
);
MockCheckbox.displayName = "MockCheckbox";

jest.mock(
  "fidesui",
  () =>
    new Proxy(jest.requireActual("fidesui"), {
      get(target, prop) {
        if (prop === "Checkbox") {
          return MockCheckbox;
        }
        return target[prop as keyof typeof target];
      },
    }),
);

const renderPicker = (value: string[] = [], onChange = jest.fn()) =>
  render(<ScopePicker value={value} onChange={onChange} />);

describe("ScopePicker", () => {
  describe("rendering", () => {
    it("renders the scope picker container", () => {
      renderPicker();
      expect(screen.getByTestId("scope-picker")).toBeInTheDocument();
    });

    it("renders the search input", () => {
      renderPicker();
      expect(
        screen.getByPlaceholderText("Filter scopes..."),
      ).toBeInTheDocument();
    });

    it("renders the select all checkbox", () => {
      renderPicker();
      expect(screen.getByTestId("scope-select-all")).toBeInTheDocument();
    });

    it("renders the client scope group", () => {
      renderPicker();
      expect(screen.getByTestId("scope-group-client")).toBeInTheDocument();
    });

    it("renders individual scope checkboxes for the client group", () => {
      renderPicker();
      expect(
        screen.getByTestId("scope-checkbox-client:create"),
      ).toBeInTheDocument();
      expect(
        screen.getByTestId("scope-checkbox-client:read"),
      ).toBeInTheDocument();
    });

    it("always shows the selected count even when zero", () => {
      renderPicker([]);
      expect(screen.getByTestId("scope-selected-count")).toHaveTextContent(
        "0 scopes selected",
      );
    });

    it("shows singular 'scope' when exactly one is selected", () => {
      renderPicker(["client:create"]);
      expect(screen.getByTestId("scope-selected-count")).toHaveTextContent(
        "1 scope selected",
      );
    });

    it("shows plural 'scopes' when multiple are selected", () => {
      renderPicker(["client:create", "client:read"]);
      expect(screen.getByTestId("scope-selected-count")).toHaveTextContent(
        "2 scopes selected",
      );
    });
  });

  describe("individual scope toggle", () => {
    it("calls onChange with scope added when checked", async () => {
      const onChange = jest.fn();
      const user = userEvent.setup();
      renderPicker([], onChange);

      await user.click(screen.getByTestId("scope-checkbox-client:create"));

      expect(onChange).toHaveBeenCalledWith(
        expect.arrayContaining(["client:create"]),
      );
    });

    it("calls onChange with scope removed when unchecked", async () => {
      const onChange = jest.fn();
      const user = userEvent.setup();
      renderPicker(["client:create", "client:read"], onChange);

      await user.click(screen.getByTestId("scope-checkbox-client:create"));

      const result = onChange.mock.calls[0][0];
      expect(result).not.toContain("client:create");
      expect(result).toContain("client:read");
    });

    it("reflects checked state from value prop", () => {
      renderPicker(["client:create"]);
      expect(screen.getByTestId("scope-checkbox-client:create")).toBeChecked();
      expect(
        screen.getByTestId("scope-checkbox-client:read"),
      ).not.toBeChecked();
    });
  });

  describe("group toggle", () => {
    it("adds all group scopes when group checkbox is checked", async () => {
      const onChange = jest.fn();
      const user = userEvent.setup();
      renderPicker([], onChange);

      await user.click(screen.getByTestId("scope-group-client"));

      const result = onChange.mock.calls[0][0];
      expect(result).toContain("client:create");
      expect(result).toContain("client:read");
      expect(result).toContain("client:update");
      expect(result).toContain("client:delete");
    });

    it("removes all group scopes when group checkbox is unchecked", async () => {
      const onChange = jest.fn();
      const user = userEvent.setup();
      renderPicker(
        ["client:create", "client:read", "client:update", "client:delete"],
        onChange,
      );

      await user.click(screen.getByTestId("scope-group-client"));

      const result = onChange.mock.calls[0][0];
      expect(result).not.toContain("client:create");
      expect(result).not.toContain("client:read");
    });

    it("group checkbox is checked when all group scopes are selected", () => {
      renderPicker([
        "client:create",
        "client:read",
        "client:update",
        "client:delete",
      ]);
      expect(screen.getByTestId("scope-group-client")).toBeChecked();
    });

    it("group checkbox is indeterminate when some group scopes are selected", () => {
      renderPicker(["client:create"]);
      const groupCheckbox = screen.getByTestId(
        "scope-group-client",
      ) as HTMLInputElement;
      expect(groupCheckbox.indeterminate).toBe(true);
    });

    it("group checkbox is unchecked when no group scopes are selected", () => {
      renderPicker([]);
      expect(screen.getByTestId("scope-group-client")).not.toBeChecked();
    });

    it("preserves scopes from other groups when toggling a group off", async () => {
      const onChange = jest.fn();
      const user = userEvent.setup();
      renderPicker(
        [
          "client:create",
          "client:read",
          "client:update",
          "client:delete",
          "user:read",
        ],
        onChange,
      );

      await user.click(screen.getByTestId("scope-group-client"));

      const result = onChange.mock.calls[0][0];
      expect(result).toContain("user:read");
    });
  });

  describe("select all", () => {
    it("calls onChange with all scopes when select-all is checked", async () => {
      const onChange = jest.fn();
      const user = userEvent.setup();
      renderPicker([], onChange);

      await user.click(screen.getByTestId("scope-select-all"));

      const result = onChange.mock.calls[0][0];
      expect(result.length).toBeGreaterThan(10);
      expect(result).toContain("client:create");
    });

    it("calls onChange with empty array when select-all is unchecked", async () => {
      const onChange = jest.fn();
      const user = userEvent.setup();
      const allScopes = Object.values(ScopeRegistryEnum) as string[];

      // Start with everything selected so the checkbox is in checked (not indeterminate) state
      render(<ScopePicker value={allScopes} onChange={onChange} />);

      await user.click(screen.getByTestId("scope-select-all"));

      expect(onChange).toHaveBeenCalledWith([]);
    });

    it("select-all is checked when all scopes are selected", () => {
      const allScopes = Object.values(ScopeRegistryEnum) as string[];
      renderPicker(allScopes);
      expect(screen.getByTestId("scope-select-all")).toBeChecked();
    });

    it("select-all is indeterminate when some scopes are selected", () => {
      renderPicker(["client:create"]);
      const checkbox = screen.getByTestId(
        "scope-select-all",
      ) as HTMLInputElement;
      expect(checkbox.indeterminate).toBe(true);
    });
  });

  describe("search filtering", () => {
    it("filters scopes by action name", async () => {
      const user = userEvent.setup();
      renderPicker();

      await user.type(
        screen.getByPlaceholderText("Filter scopes..."),
        "create",
      );

      // client:create should still be visible
      expect(
        screen.getByTestId("scope-checkbox-client:create"),
      ).toBeInTheDocument();
    });

    it("hides scopes that don't match the search", async () => {
      const user = userEvent.setup();
      renderPicker();

      // Type something very specific that won't match client:read
      await user.type(
        screen.getByPlaceholderText("Filter scopes..."),
        "xyznotareal",
      );

      expect(
        screen.queryByTestId("scope-checkbox-client:read"),
      ).not.toBeInTheDocument();
    });

    it("shows all scopes in a group when the group label matches", async () => {
      const user = userEvent.setup();
      renderPicker();

      // "client" matches the "Client" group label
      await user.type(
        screen.getByPlaceholderText("Filter scopes..."),
        "client",
      );

      // All client scopes should be visible, not just ones containing "client" in action
      expect(
        screen.getByTestId("scope-checkbox-client:create"),
      ).toBeInTheDocument();
      expect(
        screen.getByTestId("scope-checkbox-client:delete"),
      ).toBeInTheDocument();
    });

    it("shows 'no scopes match' empty state when search has no results", async () => {
      const user = userEvent.setup();
      renderPicker();

      await user.type(
        screen.getByPlaceholderText("Filter scopes..."),
        "xyznotarealscope99",
      );

      expect(screen.getByTestId("scope-picker-list")).toHaveTextContent(
        "No scopes match",
      );
    });

    it("restores all groups when search is cleared", async () => {
      const user = userEvent.setup();
      renderPicker();
      const input = screen.getByPlaceholderText("Filter scopes...");

      await user.type(input, "xyznotarealscope99");
      expect(
        screen.queryByTestId("scope-group-client"),
      ).not.toBeInTheDocument();

      await user.clear(input);
      expect(screen.getByTestId("scope-group-client")).toBeInTheDocument();
    });
  });
});
