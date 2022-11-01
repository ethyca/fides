import { useRouter } from "next/router";
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
  redirectUrl: string;
  authenticatedBlock: JSX.Element;
  children: JSX.Element;
}

const ProtectedRoute = ({
  children,
  redirectUrl,
  authenticatedBlock,
}: ProtectedRouteProps) => {
  const authenticated = useProtectedRoute(redirectUrl);
  return authenticated ? children : authenticatedBlock;
};

ProtectedRoute.defaultProps = {
  authenticatedBlock: null,
  redirectUrl: LOGIN_ROUTE,
};

export default ProtectedRoute;
