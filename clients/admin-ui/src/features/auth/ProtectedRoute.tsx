import { canAccessRoute } from "@fidesui/components";
import { useRouter } from "next/router";
import { ReactNode } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { LOGIN_ROUTE, VERIFY_AUTH_INTERVAL } from "~/constants";
import { useGetUserPermissionsQuery } from "~/features/user-management";

import { logout, selectToken, selectUser } from "./auth.slice";

const useProtectedRoute = (redirectUrl: string) => {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const token = useAppSelector(selectToken);
  const user = useAppSelector(selectUser);
  const userId = user?.id;
  const permissionsQuery = useGetUserPermissionsQuery(userId!, {
    pollingInterval: VERIFY_AUTH_INTERVAL,
    skip: !userId,
  });

  if (!token || !userId || permissionsQuery.isError) {
    // Reset the user information in redux only if we have stale information
    if (token || userId) {
      dispatch(logout());
    }
    if (typeof window !== "undefined") {
      router.push(redirectUrl);
    }
    return { authenticated: false, hasAccess: false };
  }

  const path = router.pathname;
  const userScopes = permissionsQuery.data
    ? permissionsQuery.data.total_scopes
    : [];

  const hasAccess = canAccessRoute({ path, userScopes });
  if (
    !hasAccess &&
    permissionsQuery.isSuccess &&
    typeof window !== "undefined"
  ) {
    router.push("/");
  }

  return {
    authenticated: permissionsQuery.isSuccess,
    hasAccess,
  };
};

interface ProtectedRouteProps {
  children: ReactNode;
  redirectUrl?: string;
}

const ProtectedRoute = ({
  children,
  redirectUrl = LOGIN_ROUTE,
}: ProtectedRouteProps) => {
  const { authenticated, hasAccess } = useProtectedRoute(redirectUrl);

  // Prevents the children from "flashing" on the screen before the hasAccess redirect
  if (!hasAccess) {
    return null;
  }

  // Silly type error: https://github.com/DefinitelyTyped/DefinitelyTyped/issues/18051
  // eslint-disable-next-line react/jsx-no-useless-fragment
  return authenticated ? <>{children}</> : null;
};

export default ProtectedRoute;
