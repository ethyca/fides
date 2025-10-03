import { Spinner } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";

import Layout from "~/features/common/Layout";
import { NOTIFICATIONS_TEMPLATES_ROUTE } from "~/features/common/nav/routes";

/**
 * Redirect page that automatically redirects to the Templates tab
 */
const NotificationsRedirect: NextPage = () => {
  const router = useRouter();

  useEffect(() => {
    router.replace(NOTIFICATIONS_TEMPLATES_ROUTE);
  }, [router]);

  return (
    <Layout title="Notifications">
      <div className="flex h-screen items-center justify-center">
        <Spinner />
      </div>
    </Layout>
  );
};

export default NotificationsRedirect;
