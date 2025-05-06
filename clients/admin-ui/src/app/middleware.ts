import { isRejectedWithValue, Middleware } from "@reduxjs/toolkit";
import { createStandaloneToast } from "fidesui";

import { DEFAULT_TOAST_PARAMS } from "~/features/common/toast";

const printReduxError = (action: unknown) =>
  // eslint-disable-next-line no-console
  console.error("Admin UI encountered the following error: ", action);

const { toast } = createStandaloneToast({
  defaultOptions: DEFAULT_TOAST_PARAMS,
});

export const rtkQueryErrorLogger: Middleware =
  (state) => (next) => (action) => {
    console.log({ action, state: state.getState() });
    if (isRejectedWithValue(action)) {
      const payload = action?.payload as any;
      toast({
        status: "error",
        title: payload?.status ?? "An error occured",
        description:
          action?.error?.message ??
          payload?.error ??
          "An error occurred please check the console for more detail.",
      });
      printReduxError(action);
    }
    next(action);
  };

export const testRtkQueryErrorLogger: Middleware =
  (state) => (next) => (action) => {
    if (isRejectedWithValue(action)) {
      // select value from state,
      // compare state to dictionary
      // do requested action
      printReduxError(action);
    }
    next(action);
  };
