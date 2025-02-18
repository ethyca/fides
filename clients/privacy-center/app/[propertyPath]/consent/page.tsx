import Custom404 from "~/app/not-found";
import getPrivacyCenterEnvironmentCached from "~/app/server-utils/getPrivacyCenterEnvironment";
import ConsentPage from "~/components/ConsentPage";
import PageLayout from "~/components/PageLayout";

interface CustomPropertyPathConsentPageProps {
  params: Promise<{
    propertyPath: string;
  }>;
}

/**
 * Renders the consent page for a custom property path.
 * If the property is not found, renders a 404 page.
 */
const CustomPropertyPathConsentPage = async ({
  params,
}: CustomPropertyPathConsentPageProps) => {
  const { propertyPath } = await params;
  const serverEnvironment = await getPrivacyCenterEnvironmentCached({
    propertyPath: `/${propertyPath}`,
  });
  const isPropertyFoundForPath = !!serverEnvironment.property;

  return (
    <PageLayout serverEnvironment={serverEnvironment}>
      {/* @ts-expect-error Async Server Component. Remove when upgraded to TypeScript 5.1.3 or higher. */}
      {isPropertyFoundForPath ? <ConsentPage /> : <Custom404 />}
    </PageLayout>
  );
};

export default CustomPropertyPathConsentPage;
