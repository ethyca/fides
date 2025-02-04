"use client";

import { useMemo } from "react";
import { Provider } from "react-redux";

import { loadConfig } from "~/features/common/config.slice";
import { loadProperty } from "~/features/common/property.slice";
import { loadSettings } from "~/features/common/settings.slice";
import { loadStyles } from "~/features/common/styles.slice";

import HomePage from "./HomePage";
import store from "./store";

const HomePageContainer = ({ serverEnvironment }) => {
  useMemo(() => {
    if (serverEnvironment) {
      // Load the server environment into the Redux store
      store.dispatch(loadSettings(serverEnvironment.settings));
      store.dispatch(loadConfig(serverEnvironment.config));
      store.dispatch(loadStyles(serverEnvironment.styles));
      store.dispatch(loadProperty(serverEnvironment.property));
    }
  }, [serverEnvironment]);

  return (
    <Provider store={store}>
      <HomePage />
    </Provider>
  );
};
export default HomePageContainer;
