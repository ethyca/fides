import { isRejectedWithValue, Middleware } from "@reduxjs/toolkit";
import { createStandaloneToast } from "fidesui";

import { DEFAULT_TOAST_PARAMS } from "~/features/common/toast";

const printReduxError = (action: unknown) =>
  // eslint-disable-next-line no-console
  console.error("Admin UI encountered the following error: ", action);

const { toast } = createStandaloneToast({
  defaultOptions: DEFAULT_TOAST_PARAMS,
});

export const rtkQueryErrorLogger: Middleware = () => (next) => (action) => {
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

export const testRtkQueryErrorLogger: Middleware = () => (next) => (action) => {
  if (isRejectedWithValue(action)) {
    printReduxError(action);
  }
  next(action);
};
