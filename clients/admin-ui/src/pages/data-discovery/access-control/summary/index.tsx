import { Spin } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";

import Layout from "~/features/common/Layout";
import { ACCESS_CONTROL_ROUTE } from "~/features/common/nav/routes";

const AccessControlSummaryRedirect: NextPage = () => {
  const router = useRouter();

  useEffect(() => {
    router.replace(ACCESS_CONTROL_ROUTE);
  }, [router]);

  return (
    <Layout title="Access control">
      <div className="flex h-screen items-center justify-center">
        <Spin />
      </div>
    </Layout>
  );
};

export default AccessControlSummaryRedirect;
