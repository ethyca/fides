import { useRouter } from "next/router";
import { ReactNode } from "react";
import { useDispatch, useSelector } from "react-redux";

import { LOGIN_ROUTE, VERIFY_AUTH_INTERVAL } from "~/constants";
import { canAccessRoute } from "~/features/common/nav/v2/nav-config";
import { useGetUserPermissionsQuery } from "~/features/user-management";
import { ScopeRegistry } from "~/types/api";

import { logout, selectToken, selectUser } from "./auth.slice";

const useProtectedRoute = (redirectUrl: string) => {
  const router = useRouter();
  const dispatch = useDispatch();
  const token = useSelector(selectToken);
  const user = useSelector(selectUser);
  const userId = user?.id;
  const permissionsQuery = useGetUserPermissionsQuery(userId!, {
    pollingInterval: VERIFY_AUTH_INTERVAL,
    skip: !userId,
  });

  if (!token || !userId || permissionsQuery.isError) {
    dispatch(logout());
    if (typeof window !== "undefined") {
      router.push(redirectUrl);
    }
    return { authenticated: false, hasAccess: false };
  }

  const path = router.pathname;
  const userScopes = permissionsQuery.data
    ? (permissionsQuery.data.scopes as ScopeRegistry[])
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
  const { authenticated } = useProtectedRoute(redirectUrl);

  // Silly type error: https://github.com/DefinitelyTyped/DefinitelyTyped/issues/18051
  // eslint-disable-next-line react/jsx-no-useless-fragment
  return authenticated ? <>{children}</> : null;
};

export default ProtectedRoute;
