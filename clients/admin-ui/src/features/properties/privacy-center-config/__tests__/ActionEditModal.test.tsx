import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ActionEditModal } from "../ActionEditModal";

// Test adaptation: antd's Select inside an antd Modal triggers a known jsdom +
// nwsapi crash ("e.parentElement.querySelectorAll(...).includes is not a
// function") when the dropdown's virtual list layer mounts. Other tests in this
// repo (e.g. AssessmentSettingsModal.test) mock fidesui's Select with a native
// <select> for the same reason.
jest.mock(
  "fidesui",
  () =>
    new Proxy(jest.requireActual("fidesui"), {
      get(target, prop) {
        if (prop === "Select") {
          const MockAntSelect = ({
            value,
            onChange,
            options,
            ...props
          }: any) => (
            <select
              {...props}
              value={value ?? ""}
              onChange={(e) => onChange?.(e.target.value || null)}
            >
              <option value="">Select...</option>
              {options?.map((opt: any) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          );
          MockAntSelect.displayName = "MockAntSelect";
          return MockAntSelect;
        }
        return Reflect.get(target, prop);
      },
    }),
);

describe("ActionEditModal", () => {
  it("submits a new action with required fields", async () => {
    const onOk = jest.fn();
    render(
      <ActionEditModal open initial={null} onCancel={jest.fn()} onOk={onOk} />,
    );

    await userEvent.type(
      screen.getByLabelText(/policy key/i),
      "default_access_policy",
    );
    await userEvent.type(screen.getByLabelText(/^title/i), "Access My Data");
    await userEvent.type(
      screen.getByLabelText(/description/i),
      "Request a copy.",
    );
    await userEvent.type(screen.getByLabelText(/icon path/i), "/icon.svg");
    await userEvent.click(screen.getByRole("button", { name: /save/i }));

    expect(onOk).toHaveBeenCalledWith(
      expect.objectContaining({
        policy_key: "default_access_policy",
        title: "Access My Data",
        description: "Request a copy.",
        icon_path: "/icon.svg",
      }),
    );
  });
});
