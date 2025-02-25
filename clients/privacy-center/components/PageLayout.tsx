import { PrivacyCenterEnvironment } from "~/app/server-environment";

import Header from "./Header";
import Providers from "./Providers";

interface PageLayoutProps {
  children: React.ReactNode;
  serverEnvironment: PrivacyCenterEnvironment;
}

const PageLayout = ({ children, serverEnvironment }: PageLayoutProps) => {
  const { config } = serverEnvironment;
  return (
    <>
      <Header logoPath={config?.logo_path!} logoUrl={config?.logo_url!} />
      <div>
        <Providers serverEnvironment={serverEnvironment}>{children}</Providers>
      </div>
    </>
  );
};
export default PageLayout;
