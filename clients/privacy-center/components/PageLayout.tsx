"use client";

import { useConfig } from "~/features/common/config.slice";

import CustomStylesWrapper from "./CustomStylesWrapper";
import Header from "./Header";

interface PageLayoutProps {
  children: React.ReactNode;
  nonce: string | null;
}

const PageLayout = ({ children, nonce }: PageLayoutProps) => {
  const config = useConfig();

  return (
    <CustomStylesWrapper nonce={nonce}>
      <Header logoPath={config?.logo_path!} logoUrl={config?.logo_url!} />
      {children}
    </CustomStylesWrapper>
  );
};
export default PageLayout;
