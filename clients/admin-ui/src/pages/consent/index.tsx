import { ChakraCenter as Center, Spin } from "fidesui";
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
      <Center>
        <Spin />
      </Center>
    </Layout>
  );
};

export default ConsentPage;
