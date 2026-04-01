import { Spin } from "fidesui";
import { useRouter } from "next/router";
import { useEffect } from "react";

import Layout from "~/features/common/Layout";
import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/routes";

const ConsentPage = () => {
  const router = useRouter();

  useEffect(() => {
    router.push(PRIVACY_NOTICES_ROUTE);
  }, [router]);

  return (
    <Layout title="Consent">
      <Spin />
    </Layout>
  );
};

export default ConsentPage;
