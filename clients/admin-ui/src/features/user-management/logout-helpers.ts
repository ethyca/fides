import { NextRouter } from "next/router";
import { AppDispatch } from "~/app/store";
import { LOGIN_ROUTE, STORAGE_ROOT_KEY } from "~/constants";
import { logout } from "~/features/auth/auth.slice";

export const clearAuthAndLogout = (
  dispatch: AppDispatch,
  router: NextRouter,
  opts?: { onClose?: () => void },
) => {
  try {
    localStorage.removeItem(STORAGE_ROOT_KEY);
  } catch (e) {
    // no-op
  }
  dispatch(logout());
  opts?.onClose?.();
  router.push(LOGIN_ROUTE);
};
