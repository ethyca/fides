import ProductCardMetrics from "./ProductCardMetrics";
import ProductCardMinimal from "./ProductCardMinimal";
import { type ProductId, PRODUCTS } from "./products";

export type ProductCardVariant = "minimal" | "metrics";

interface ProductGridProps {
  variant: ProductCardVariant;
  onSelect: (id: ProductId) => void;
}

const ProductGrid = ({ variant, onSelect }: ProductGridProps) => {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gridTemplateRows: "1fr 1fr",
        gap: 20,
        width: "100%",
        height: "100%",
      }}
    >
      {PRODUCTS.map((product, i) =>
        variant === "minimal" ? (
          <ProductCardMinimal
            key={product.id}
            product={product}
            onSelect={onSelect}
            index={i}
          />
        ) : (
          <ProductCardMetrics
            key={product.id}
            product={product}
            onSelect={onSelect}
            index={i}
          />
        ),
      )}
    </div>
  );
};

export default ProductGrid;
