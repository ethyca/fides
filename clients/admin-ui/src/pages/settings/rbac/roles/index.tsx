import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";

import { RBAC_ROUTE } from "~/features/common/nav/routes";

// Redirect to main RBAC page
const RolesIndexPage: NextPage = () => {
  const router = useRouter();

  useEffect(() => {
    router.replace(RBAC_ROUTE);
  }, [router]);

  return null;
};

export default RolesIndexPage;
