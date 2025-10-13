import { Spinner } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import {
  MESSAGING_PROVIDERS_ROUTE,
  NOTIFICATIONS_TEMPLATES_ROUTE,
} from "~/features/common/nav/routes";

/**
 * Redirect page that automatically redirects to the first available tab.
 * If Plus is enabled, redirects to Templates tab.
 * Otherwise, redirects to Digests tab.
 */
const NotificationsRedirect: NextPage = () => {
  const router = useRouter();
  const { plus } = useFeatures();

  useEffect(() => {
    // Redirect to Templates if Plus, otherwise to Digests
    const targetRoute = plus
      ? NOTIFICATIONS_TEMPLATES_ROUTE
      : MESSAGING_PROVIDERS_ROUTE;
    router.push(targetRoute);
  }, [router, plus]);

  return (
    <Layout title="Notifications">
      <div className="flex h-screen items-center justify-center">
        <Spinner />
      </div>
    </Layout>
  );
};

export default NotificationsRedirect;
