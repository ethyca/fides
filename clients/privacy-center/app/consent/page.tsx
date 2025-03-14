"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import ConsentPage from "~/components/ConsentPage";
import PageLayout from "~/components/PageLayout";
import { useHasConfig } from "~/features/common/config.slice";

/**
 * Renders the consent page for the privacy center.
 * This is a client component that relies on having the config loaded into the providers by the homepage component.
 * If the config is not loaded, it redirect to the homepage
 */

const Consent = () => {
  const hasConfig = useHasConfig();
  const router = useRouter();

  useEffect(() => {
    if (!hasConfig) {
      router.push(`/`);
    }
  }, [hasConfig, router]);

  if (!hasConfig) {
    return null;
  }

  return (
    <PageLayout>
      <ConsentPage />
    </PageLayout>
  );
};

export default Consent;
