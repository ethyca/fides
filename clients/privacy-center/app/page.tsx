"use client";

import { Provider } from "react-redux";

import Home from "./homepage";
import store from "./store";

const HomePage = () => {
  return (
    <Provider store={store}>
      <Home />
    </Provider>
  );
};

export default HomePage;
