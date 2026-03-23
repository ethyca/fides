import { Spin } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";

import Layout from "~/features/common/Layout";
import { ACCESS_CONTROL_ROUTE } from "~/features/common/nav/routes";

const AccessControlRequestLogRedirect: NextPage = () => {
  const router = useRouter();

  useEffect(() => {
    const { policy, control } = router.query;
    const params = new URLSearchParams();
    params.set("tab", "log");
    if (typeof policy === "string") {
      params.set("policy", policy);
    }
    if (typeof control === "string") {
      params.set("control", control);
    }
    router.replace(`${ACCESS_CONTROL_ROUTE}?${params.toString()}`);
  }, [router]);

  return (
    <Layout title="Access control">
      <div className="flex h-screen items-center justify-center">
        <Spin />
      </div>
    </Layout>
  );
};

export default AccessControlRequestLogRedirect;
