import { useRouter } from "next/router";
import { ReactNode } from "react";
import { useDispatch, useSelector } from "react-redux";

import { LOGIN_ROUTE, VERIFY_AUTH_INTERVAL } from "~/constants";
import { useGetUserPermissionsQuery } from "~/features/user-management";

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
    return false;
  }

  return permissionsQuery.isSuccess;
};

interface ProtectedRouteProps {
  children: ReactNode;
  redirectUrl?: string;
}

const ProtectedRoute = ({
  children,
  redirectUrl = LOGIN_ROUTE,
}: ProtectedRouteProps) => {
  const authenticated = useProtectedRoute(redirectUrl);

  // Silly type error: https://github.com/DefinitelyTyped/DefinitelyTyped/issues/18051
  // eslint-disable-next-line react/jsx-no-useless-fragment
  return authenticated ? <>{children}</> : null;
};

export default ProtectedRoute;
