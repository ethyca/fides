import { EthycaLogo, Link, LinkProps } from "fidesui";

import { useSettings } from "~/features/common/settings.slice";

const BrandLink = ({
  position = "absolute",
  right = 6,
  ...props
}: LinkProps) => {
  const { SHOW_BRAND_LINK } = useSettings();

  if (!SHOW_BRAND_LINK) {
    return null;
  }

  return (
    <Link
      fontSize="8px"
      color="gray.400"
      isExternal
      position={position}
      right={right}
      textDecoration="none"
      _hover={{ textDecoration: "none" }}
      {...props}
    >
      Powered by <EthycaLogo color="minos.500" h="20px" w="31px" />
    </Link>
  );
};

export default BrandLink;
