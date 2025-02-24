// test-utils.jsx
import { Store } from "@reduxjs/toolkit";
import { render as rtlRender, RenderOptions } from "@testing-library/react";
import React, { ReactNode } from "react";
import { Provider } from "react-redux";

import { makeStore } from "~/app/store";

type CustomRenderOptions = {
  preloadedState?: any;
  customStore?: Store;
} & RenderOptions;

function render(
  ui: React.ReactElement<any, string | React.JSXElementConstructor<any>>,
  {
    preloadedState,
    customStore = makeStore(preloadedState),
    ...renderOptions
  }: CustomRenderOptions = {},
) {
  const Wrapper = ({ children }: { children: ReactNode }) => (
    <Provider store={customStore}>{children}</Provider>
  );
  return rtlRender(ui, { wrapper: Wrapper, ...renderOptions });
}

// re-export everything
export * from "@testing-library/react";

// override render method
export { render };

// Mocks useRouter
const useRouter = jest.spyOn(require("next/router"), "useRouter");

/**
 * mockNextUseRouter
 * Mocks the useRouter React hook from Next.js on a test-case by test-case basis
 * Adapted from https://github.com/vercel/next.js/issues/7479#issuecomment-587145429
 */
export function mockNextUseRouter({
  route = "/",
  pathname = "/",
  query = "/",
  asPath = "/",
}: {
  route?: string;
  pathname?: string;
  query?: string;
  asPath?: string;
}) {
  useRouter.mockImplementation(() => ({
    route,
    pathname,
    query,
    asPath,
  }));
}
