import { useRouter } from "next/router";
import { useSelector } from "react-redux";

import { selectToken } from "./auth.slice";

const useProtectedRoute = (redirectUrl: string) => {
  const router = useRouter();
  const token = useSelector(selectToken);

  // TODO: check for token invalidation
  if (!token && typeof window !== "undefined") {
    router.push(redirectUrl);
    return false;
  }

  return true;
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
  redirectUrl: "/login",
};

export default ProtectedRoute;
