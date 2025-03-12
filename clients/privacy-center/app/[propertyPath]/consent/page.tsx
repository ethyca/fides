"use client";
import ConsentPage from "~/components/ConsentPage";
import PageLayout from "~/components/PageLayout";
import { useHasConfig } from "~/features/common/config.slice";
import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";

/**
 * Renders the consent page for a custom property path.
 * It relies on having the config loaded into the providers by the homepage component.
 * If the config is not loaded, it will redirect to the property home path.
 */
const CustomPropertyPathConsentPage = () => {
  const hasConfig = useHasConfig();
  const router = useRouter();
  const params = useParams();

  useEffect(() => {
    if (!hasConfig) {
      router.push(`/${params?.propertyPath}`);
    }
  }, [hasConfig]);

  if (!hasConfig) {
    return null;
  }

  return (
    <PageLayout>
      <ConsentPage />
    </PageLayout>
  );
};

export default CustomPropertyPathConsentPage;
