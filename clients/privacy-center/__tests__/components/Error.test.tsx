/**
 * @jest-environment jsdom
 */

import { configureStore } from "@reduxjs/toolkit";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { Provider } from "react-redux";

import ErrorFallback, { DEFAULT_ERROR_MESSAGE } from "~/components/Error";
import { configSlice, loadConfig } from "~/features/common/config.slice";
import { Config } from "~/types/config";

// Stub fidesui to avoid pulling its ESM-only transitive deps (e.g.
// react-hotkeys-hook) through Jest's next/jest preset, which ignores
// node_modules by default. We only need lightweight stand-ins for the
// layout primitives used by Error.tsx; behavior under test (message
// selection, logo gating, reset handler wiring) is unaffected.
jest.mock("fidesui", () => {
  // eslint-disable-next-line global-require
  const ReactMod = require("react") as typeof import("react");
  const makeBox = (tag: string) => {
    const Stub = ({ children, ...rest }: { children?: React.ReactNode }) =>
      ReactMod.createElement(tag, rest, children);
    Stub.displayName = `FidesuiStub(${tag})`;
    return Stub;
  };
  const Button = ({
    children,
    onClick,
    ...rest
  }: {
    children?: React.ReactNode;
    onClick?: () => void;
  }) =>
    ReactMod.createElement(
      "button",
      { onClick, type: "button", ...rest },
      children,
    );
  Button.displayName = "FidesuiStub(Button)";
  // Pass through the real element so onError/onLoad handlers can be fired by
  // tests. Omit the hardcoded data-testid — the component sets its own.
  const ChakraImage = (props: Record<string, unknown>) =>
    ReactMod.createElement("img", props);
  ChakraImage.displayName = "FidesuiStub(ChakraImage)";
  const ChakraLink = ({
    children,
    href,
  }: {
    children?: React.ReactNode;
    href?: string;
  }) => ReactMod.createElement("a", { href }, children);
  ChakraLink.displayName = "FidesuiStub(ChakraLink)";
  return {
    __esModule: true,
    Button,
    ChakraBox: makeBox("div"),
    ChakraFlex: makeBox("div"),
    ChakraHeading: makeBox("h1"),
    ChakraStack: makeBox("div"),
    ChakraText: makeBox("p"),
    ChakraImage,
    ChakraLink,
  };
});

const SENSITIVE_ERROR_MESSAGE =
  "Cannot read properties of undefined (reading 'trim')";

// Build a minimal test-only store with just the config slice so we don't
// transitively import modules (e.g. fidesui hotkey hooks) that Jest's
// next/jest transform doesn't handle out of the box.
const makeTestStore = () =>
  configureStore({
    reducer: { [configSlice.name]: configSlice.reducer },
  });

const renderErrorFallback = (preloadedConfig?: Partial<Config>) => {
  const store = makeTestStore();
  if (preloadedConfig !== undefined) {
    store.dispatch(loadConfig(preloadedConfig as unknown as Config));
  }
  const resetErrorBoundary = jest.fn();
  const boundaryError = new Error(SENSITIVE_ERROR_MESSAGE);
  const utils = render(
    <Provider store={store}>
      <ErrorFallback
        error={boundaryError}
        resetErrorBoundary={resetErrorBoundary}
      />
    </Provider>,
  );
  return { ...utils, resetErrorBoundary, boundaryError };
};

describe("Error fallback", () => {
  it("renders the configured error_message when present", () => {
    renderErrorFallback({ error_message: "Our team is on it, please hold." });

    expect(
      screen.getByText("Our team is on it, please hold."),
    ).toBeInTheDocument();
    expect(screen.queryByText(DEFAULT_ERROR_MESSAGE)).not.toBeInTheDocument();
  });

  it("falls back to the default message when error_message is not set", () => {
    renderErrorFallback({});

    expect(screen.getByText(DEFAULT_ERROR_MESSAGE)).toBeInTheDocument();
  });

  it("falls back to the default message when the config slice is uninitialized", () => {
    // Simulates the worst case: the error fired before config finished loading.
    renderErrorFallback();

    expect(screen.getByText(DEFAULT_ERROR_MESSAGE)).toBeInTheDocument();
  });

  it("falls back to the default message when error_message is an empty/whitespace string", () => {
    renderErrorFallback({ error_message: "   " });

    expect(screen.getByText(DEFAULT_ERROR_MESSAGE)).toBeInTheDocument();
  });

  it("never exposes the raw error message to the user", () => {
    renderErrorFallback({ error_message: "Custom message" });

    expect(screen.queryByText(SENSITIVE_ERROR_MESSAGE)).not.toBeInTheDocument();
    expect(
      screen.queryByText(new RegExp(SENSITIVE_ERROR_MESSAGE, "i")),
    ).not.toBeInTheDocument();
  });

  it("renders the configured logo when logo_path is present", () => {
    renderErrorFallback({ logo_path: "/tenant-logo.svg" });

    const logo = screen.getByTestId("logo");
    expect(logo).toBeInTheDocument();
    expect(logo).toHaveAttribute("src", "/tenant-logo.svg");
  });

  it("omits the logo bar when logo_path is not configured", () => {
    renderErrorFallback();

    expect(screen.queryByTestId("logo")).not.toBeInTheDocument();
  });

  it("hides the logo bar when the configured asset fails to load", () => {
    renderErrorFallback({ logo_path: "/missing.svg" });

    const logo = screen.getByTestId("logo");
    fireEvent.error(logo);

    expect(screen.queryByTestId("logo")).not.toBeInTheDocument();
  });

  it("invokes resetErrorBoundary when the user clicks 'Try again'", async () => {
    const user = userEvent.setup();
    const { resetErrorBoundary } = renderErrorFallback();

    await user.click(screen.getByRole("button", { name: /try again/i }));

    expect(resetErrorBoundary).toHaveBeenCalledTimes(1);
  });
});
