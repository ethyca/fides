import { render, screen } from "@testing-library/react";
import { Form } from "fidesui";

import { SwitchField } from "./SwitchField";

const Wrapper = ({
  children,
  initialValues = {},
}: {
  children: React.ReactNode;
  initialValues?: Record<string, unknown>;
}) => {
  const [form] = Form.useForm();
  return (
    <Form form={form} initialValues={initialValues}>
      {children}
    </Form>
  );
};

describe("SwitchField", () => {
  it("renders label text", () => {
    render(
      <Wrapper initialValues={{ dismissable: true }}>
        <SwitchField name="dismissable" label="Allow user to dismiss" />
      </Wrapper>,
    );
    expect(screen.getByText("Allow user to dismiss")).toBeInTheDocument();
  });

  it("renders switch with correct data-testid", () => {
    render(
      <Wrapper initialValues={{ dismissable: false }}>
        <SwitchField name="dismissable" label="Allow user to dismiss" />
      </Wrapper>,
    );
    expect(screen.getByTestId("input-dismissable")).toBeInTheDocument();
  });

  it("renders switch as disabled via switchProps", () => {
    render(
      <Wrapper initialValues={{ dismissable: false }}>
        <SwitchField
          name="dismissable"
          label="Allow user to dismiss"
          switchProps={{ disabled: true }}
        />
      </Wrapper>,
    );
    const switchEl = screen.getByTestId("input-dismissable");
    expect(switchEl).toBeDisabled();
  });

  it("renders switch as enabled when switchProps.disabled is not set", () => {
    render(
      <Wrapper initialValues={{ dismissable: false }}>
        <SwitchField name="dismissable" label="Allow user to dismiss" />
      </Wrapper>,
    );
    const switchEl = screen.getByTestId("input-dismissable");
    expect(switchEl).not.toBeDisabled();
  });
});
