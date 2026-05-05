import type { ProductId } from "./products";

interface ProductIconProps {
  productId: ProductId;
  size?: number;
}

const ProductIcon = ({ productId, size = 48 }: ProductIconProps) => (
  <img
    src={`/images/${productId}.svg`}
    alt=""
    aria-hidden
    style={{ width: size, height: "auto", display: "block" }}
  />
);

export default ProductIcon;
