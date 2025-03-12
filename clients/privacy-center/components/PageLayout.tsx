"use client";
import { useConfig } from "~/features/common/config.slice";
import CustomStylesWrapper from "./CustomStylesWrapper";

import Header from "./Header";

interface PageLayoutProps {
  children: React.ReactNode;
}

const PageLayout = ({ children }: PageLayoutProps) => {
  const config = useConfig();
  return (
    <CustomStylesWrapper>
      <Header logoPath={config?.logo_path!} logoUrl={config?.logo_url!} />
      {children}
    </CustomStylesWrapper>
  );
};
export default PageLayout;
