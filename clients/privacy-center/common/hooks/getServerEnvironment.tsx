"use server";

import { headers } from "next/headers";

import { loadPrivacyCenterEnvironment } from "~/app/server-environment";

const getServerEnvironment = async () => {
  const headersList = await headers();

  // Load the server-side environment for the session and pass it to the client as props
  const customPropertyPath = headersList.get("customPropertyPath")?.toString();
  const serverEnvironment = await loadPrivacyCenterEnvironment({
    customPropertyPath,
  });
  return serverEnvironment;
};

export default getServerEnvironment;
