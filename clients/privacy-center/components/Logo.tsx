import { Image } from "@fidesui/react";
import React from "react";

type LogoProps = {
  logo_path: string;
};

const Logo: React.FC<LogoProps> = ({ logo_path }) => (
  <Image
    src={logo_path}
    margin="8px"
    height="68px"
    alt="Logo"
    data-testid="logo"
  />
);

export default Logo;
