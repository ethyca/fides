"use server";

import "./ui/global.scss";

import getServerEnvironment from "~/common/hooks/getServerEnvironment";
import Header from "~/components/Header";

import Providers from "./Providers";

export async function generateMetadata() {
  const { config } = await getServerEnvironment();

  return {
    title: "Privacy Center",
    description: "Privacy Center",
    icons: {
      icon: config?.favicon_path || "/favicon.ico",
    },
  };
}

const Layout = async ({ children }: { children: React.ReactNode }) => {
  const serverEnvironment = await getServerEnvironment();
  const { config, styles } = serverEnvironment;

  return (
    <html lang="en">
      <body>
        {styles ? <style suppressHydrationWarning>{styles}</style> : null}
        <Header logoPath={config?.logo_path!} logoUrl={config?.logo_url!} />
        <div>
          <Providers serverEnvironment={serverEnvironment}>
            {children}
          </Providers>
        </div>
      </body>
    </html>
  );
};
export default Layout;
