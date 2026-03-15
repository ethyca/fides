import { Spin } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";

import Layout from "~/features/common/Layout";
import { ACCESS_CONTROL_SUMMARY_ROUTE } from "~/features/common/nav/routes";

const AccessControlRedirect: NextPage = () => {
  const router = useRouter();

  useEffect(() => {
    router.push(ACCESS_CONTROL_SUMMARY_ROUTE);
  }, [router]);

  return (
    <Layout title="Access control">
      <div className="flex h-screen items-center justify-center">
        <Spin />
      </div>
    </Layout>
  );
};

export default AccessControlRedirect;
