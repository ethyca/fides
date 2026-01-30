import { useRouter } from "next/router";
import { ReactNode, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { LOGIN_ROUTE, VERIFY_AUTH_INTERVAL } from "~/constants";
import { useNav } from "~/features/common/nav/hooks";
import { useGetHealthQuery } from "~/features/plus/plus.slice";
import { useGetUserPermissionsQuery } from "~/features/user-management";

import { logout, selectToken, selectUser } from "./auth.slice";

const REDIRECT_IGNORES = ["/", "/login"];

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
  const plusQuery = useGetHealthQuery();
  const nav = useNav({ path: router.pathname });
  const [redirectFrom, setRedirectFrom] = useState<string | undefined>();

  if (!token || !userId || permissionsQuery.isError) {
    // Reset the user information in redux only if we have stale information
    if (token || userId) {
      dispatch(logout());
    }
    if (typeof window !== "undefined") {
      const redirectParam = REDIRECT_IGNORES.includes(window.location.pathname)
        ? ""
        : `?redirect=${encodeURIComponent(window.location.pathname)}`;
      if (
        redirectFrom !== window.location.pathname &&
        window.location.pathname !== redirectUrl
      ) {
        setRedirectFrom(window.location.pathname);
        // Use hard navigation instead of client-side navigation to ensure
        // the page fully reloads. This fixes an issue where the OIDC/SSO
        // login buttons wouldn't appear after session timeout because
        // RTK Query cache was cleared but queries didn't properly refetch
        // during client-side navigation (ENG-1466).
        window.location.href = `${redirectUrl}${redirectParam}`;
      }
    }
    return { authenticated: false, hasAccess: false };
  }

  const hasAccess = !!nav.active;
  if (
    !hasAccess &&
    permissionsQuery.isSuccess &&
    typeof window !== "undefined" &&
    !plusQuery.isLoading
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
