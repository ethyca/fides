import { isRejectedWithValue, Middleware } from "@reduxjs/toolkit";
import { createStandaloneToast } from "fidesui";

import { DEFAULT_TOAST_PARAMS } from "~/features/common/toast";
import { selectApplicationConfig } from "~/features/config-settings/config-settings.slice";
import { ErrorNotificationMode } from "~/types/api";

const printReduxError = (action: unknown) =>
  // eslint-disable-next-line no-console
  console.error("Admin UI encountered the following error: ", action);

const { toast } = createStandaloneToast({
  defaultOptions: DEFAULT_TOAST_PARAMS,
});

const errorLoggingFunctions: Record<
  ErrorNotificationMode,
  (action: unknown) => void
> = {
  console_only: printReduxError,
  toast: (action) => {
    toast({
      status: "error",
      title: "An error occured",
      description:
        "An error occurred please check the console for more detail.",
    });
    printReduxError(action);
  },
};

export const rtkQueryErrorLogger: Middleware =
  (state) => (next) => (action) => {
    if (isRejectedWithValue(action)) {
      const applicationState = selectApplicationConfig({ api_set: false })(
        state.getState(),
      );
      const loggingMode =
        applicationState?.admin_ui?.error_notification_mode ??
        ErrorNotificationMode.CONSOLE_ONLY;

      errorLoggingFunctions[loggingMode](action);
    }
    next(action);
  };
