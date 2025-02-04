import { headers } from "next/headers";

import HomePageContainer from "./HomePageContainer";
import { loadPrivacyCenterEnvironment } from "./server-environment";

const HomePage = async () => {
  const headersList = await headers();

  // Load the server-side environment for the session and pass it to the client as props
  const customPropertyPath = headersList.get("customPropertyPath")?.toString();
  const serverEnvironment = await loadPrivacyCenterEnvironment({
    customPropertyPath,
  });
  return <HomePageContainer serverEnvironment={serverEnvironment} />;
};

export default HomePage;
