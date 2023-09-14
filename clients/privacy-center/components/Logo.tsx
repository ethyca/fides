import { Image } from "@fidesui/react";
import React from "react";

import { useConfig } from "~/features/common/config.slice";

interface LayoutProps {}

const Logo: React.FC<LayoutProps> = ({ children }) => {
  const config = useConfig();
  return (
    <Image
      src={config.logo_path}
      margin="8px"
      height="68px"
      alt="Logo"
      data-testid="logo"
    />
  );
};

export default Logo;
