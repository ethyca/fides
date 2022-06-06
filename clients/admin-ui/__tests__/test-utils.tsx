// test-utils.jsx
import { render as rtlRender, RenderOptions } from '@testing-library/react';
import React from 'react';
import { Provider } from 'react-redux';

import { AppState, AppStore, makeStore } from '../src/app/store';

type CustomRenderOptions = {
  preloadedState?: AppState;
  store?: AppStore;
} & RenderOptions;

function render(
  ui: React.ReactElement<any, string | React.JSXElementConstructor<any>>,
  {
    preloadedState,
    store = makeStore(preloadedState),
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  const Wrapper: React.FC = ({ children }) => (
    <Provider store={store}>{children}</Provider>
  );
  return rtlRender(ui, { wrapper: Wrapper, ...renderOptions });
}

// re-export everything
export * from '@testing-library/react';
// override render method
export { render };
