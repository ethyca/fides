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

const IDPCallbackPage = async ({
  searchParams,
}: {
  searchParams: NextSearchParams;
}) => {
  const serverEnvironment = await getPrivacyCenterEnvironmentCached({
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

export default IDPCallbackPage;
