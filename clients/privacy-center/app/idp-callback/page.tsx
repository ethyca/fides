"use server";

import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
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
      <IDPCallbackHandler />
    </LoadServerEnvironmentIntoStores>
  );
};

export default IDPCallbackPage;
