import Image from "~/features/common/Image";

interface EthycaLogoProps {
  size?: number;
  variant?: "default" | "white";
}

/**
 * Reusable Ethyca logomark for chat avatars and branding throughout the admin UI.
 */
const EthycaLogo = ({ size = 20, variant = "default" }: EthycaLogoProps) => (
  <Image
    src={
      variant === "white"
        ? "/images/logomark-ethyca-white.svg"
        : "/images/logomark-ethyca.svg"
    }
    alt="Ethyca"
    width={size}
    height={size}
  />
);

export default EthycaLogo;
