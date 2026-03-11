import {
  ChakraLink as Link,
  ChakraLinkProps as LinkProps,
  Space,
} from "fidesui";

import { useSettings } from "~/features/common/settings.slice";

import { AttributionLink } from "./AttributionLink";
import { EthycaLogoSvg } from "./EthycaLogoSvg";

const BrandLink = ({
  isHomePage = false,
  position = "absolute",
  right = 6,
  ...props
}: LinkProps & { isHomePage?: boolean }) => {
  const {
    SHOW_BRAND_LINK,
    ATTRIBUTION_ENABLED,
    ATTRIBUTION_ANCHOR_TEXT,
    ATTRIBUTION_DESTINATION_URL,
    ATTRIBUTION_NOFOLLOW,
  } = useSettings();

  if (ATTRIBUTION_ENABLED) {
    // On the homepage, the server-rendered AttributionLink handles this.
    if (isHomePage) {
      return null;
    }
    return (
      <AttributionLink
        attribution={{
          anchorText: ATTRIBUTION_ANCHOR_TEXT,
          destinationUrl: ATTRIBUTION_DESTINATION_URL,
          nofollow: ATTRIBUTION_NOFOLLOW,
        }}
      />
    );
  }

  if (!SHOW_BRAND_LINK) {
    return null;
  }

  return (
    <Link
      fontSize="8px"
      isExternal
      position={position}
      right={right}
      textDecoration="none"
      _hover={{ textDecoration: "none" }}
      href="https://ethyca.com/"
      {...props}
    >
      <Space size={4}>
        <div style={{ color: "var(--fidesui-neutral-500)" }}>Powered by</div>
        <div style={{ color: "var(--fidesui-minos)" }}>
          <EthycaLogoSvg />
        </div>
      </Space>
    </Link>
  );
};

export default BrandLink;
