import type { ProductId } from "./products";

interface ProductIconProps {
  productId: ProductId;
  size?: number;
  color?: string;
}

const ASPECT = 44 / 48;

const ProductIcon = ({
  productId,
  size = 48,
  color = "#2b2e35",
}: ProductIconProps) => {
  const url = `/images/${productId}.svg`;
  return (
    <span
      aria-hidden
      style={{
        display: "block",
        width: size,
        height: size * ASPECT,
        backgroundColor: color,
        WebkitMaskImage: `url(${url})`,
        maskImage: `url(${url})`,
        WebkitMaskRepeat: "no-repeat",
        maskRepeat: "no-repeat",
        WebkitMaskPosition: "center",
        maskPosition: "center",
        WebkitMaskSize: "contain",
        maskSize: "contain",
      }}
    />
  );
};

export default ProductIcon;
