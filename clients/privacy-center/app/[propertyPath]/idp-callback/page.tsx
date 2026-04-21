"use server";

import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
import { AuthFormLayout } from "~/components/common/AuthFormLayout";
import LoadServerEnvironmentIntoStores from "~/components/LoadServerEnvironmentIntoStores";
import { IDPCallbackHandler } from "~/features/idp-verification";
import { NextSearchParams } from "~/types/next";

export const generateMetadata = getPageMetadata;

const PropertyPathIDPCallbackPage = async ({
  params,
  searchParams,
}: {
  params: Promise<{ propertyPath: string }>;
  searchParams: NextSearchParams;
}) => {
  const { propertyPath } = await params;
  const serverEnvironment = await getPrivacyCenterEnvironmentCached({
    propertyPath: `/${propertyPath}`,
    searchParams,
    skipGeolocation: true,
  });

  return (
    <LoadServerEnvironmentIntoStores serverEnvironment={serverEnvironment}>
      <AuthFormLayout dataTestId="idp-callback-layout">
        <IDPCallbackHandler />
      </AuthFormLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default PropertyPathIDPCallbackPage;
