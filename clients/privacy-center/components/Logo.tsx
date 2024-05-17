import { Image, Link } from "fidesui";
import React from "react";

type LogoProps = {
  src: string;
  href?: string;
};

const LogoImage = ({ src }: Pick<LogoProps, "src">) => (
  <Image src={src} margin="8px" height="68px" alt="Logo" data-testid="logo" />
);

const Logo = ({ src, href }: LogoProps) => {
  if (href) {
    return (
      <Link href={href}>
        <LogoImage src={src} />
      </Link>
    );
  }
  return <LogoImage src={src} />;
};

export default Logo;
