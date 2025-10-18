import { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";

import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";

const DataExplorerRedirect: NextPage = () => {
  const router = useRouter();

  useEffect(() => {
    router.replace(ACTION_CENTER_ROUTE);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
};

export default DataExplorerRedirect;
