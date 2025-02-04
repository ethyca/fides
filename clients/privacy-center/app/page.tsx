import getServerEnvironment from "~/common/hooks/getServerEnvironment";

import HomePageContainer from "./HomePageContainer";

const HomePage = async () => {
  const serverEnvironment = await getServerEnvironment();

  return <HomePageContainer serverEnvironment={serverEnvironment} />;
};

export default HomePage;
