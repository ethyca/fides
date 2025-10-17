import { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";

import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";

const DataExplorerRedirect: NextPage = () => {
  const router = useRouter();

  useEffect(() => {
    router.push(ACTION_CENTER_ROUTE);
  }, [router]);

  return null;
};

export default DataExplorerRedirect;
