// test-utils.jsx
import { Store } from "@reduxjs/toolkit";
import { render as rtlRender, RenderOptions } from "@testing-library/react";
import React from "react";
import { Provider } from "react-redux";

import { makeStore, RootState } from "../src/app/store";

type CustomRenderOptions = {
  preloadedState?: Partial<RootState>;
  customStore?: Store;
} & RenderOptions;

function render(
  ui: React.ReactElement<any, string | React.JSXElementConstructor<any>>,
  {
    preloadedState,
    customStore = makeStore(preloadedState),
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  const Wrapper: React.FC = ({ children }) => (
    <Provider store={customStore}>{children}</Provider>
  );
  return rtlRender(ui, { wrapper: Wrapper, ...renderOptions });
}

// re-export everything
export * from "@testing-library/react";

// override render method
export { render };
