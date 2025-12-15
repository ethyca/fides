"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";

import ConsentPage from "~/components/ConsentPage";
import { useHasConfig } from "~/features/common/config.slice";

/**
 * Renders the consent page for a custom property path.
 * It relies on having the config loaded into the providers by the homepage component.
 * If the config is not loaded, it will redirect to the property home path.
 */

const CustomPropertyPathConsentPageWrapper = () => {
  const hasConfig = useHasConfig();
  const router = useRouter();
  const params = useParams();

  useEffect(() => {
    if (!hasConfig) {
      router.push(`/${params?.propertyPath}`);
    }
  }, [hasConfig, params?.propertyPath, router]);

  if (!hasConfig) {
    return null;
  }

  return <ConsentPage />;
};

export default CustomPropertyPathConsentPageWrapper;
