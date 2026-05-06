import { motion } from "framer-motion";
import { useState } from "react";

import ProductIcon from "./ProductIcon";
import type { Product } from "./products";

const INK = "#2b2e35";
const INK_MUTED = "rgba(43,46,53,0.55)";
const INK_REST = "#A8AAAD";

interface ProductCardMinimalProps {
  product: Product;
  onSelect: (id: Product["id"]) => void;
  index?: number;
}

const ProductCardMinimal = ({
  product,
  onSelect,
  index = 0,
}: ProductCardMinimalProps) => {
  const [hover, setHover] = useState(false);
  const { name, tagline, summary, owned } = product;
  const interactive = owned;

  const handleActivate = () => {
    if (interactive) {
      onSelect(product.id);
    }
  };

  return (
    <motion.div
      role={interactive ? "button" : undefined}
      tabIndex={interactive ? 0 : undefined}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.45,
        ease: [0.22, 1, 0.36, 1],
        delay: index * 0.08,
      }}
      onClick={handleActivate}
      onKeyDown={(e) => {
        if (interactive && (e.key === "Enter" || e.key === " ")) {
          e.preventDefault();
          handleActivate();
        }
      }}
      onMouseEnter={() => interactive && setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        position: "relative",
        display: "flex",
        alignItems: "center",
        gap: 20,
        cursor: interactive ? "pointer" : "default",
        color: INK,
        width: "100%",
        height: "100%",
      }}
    >
      <div
        style={{
          width: 84,
          height: 84,
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#ffffff",
          borderRadius: 6,
          boxShadow: hover
            ? "0 4px 14px rgba(43,46,53,0.08), 0 1px 2px rgba(43,46,53,0.04)"
            : "0 1px 2px rgba(43,46,53,0.04)",
          transform: hover ? "translateY(-1px)" : "translateY(0)",
          transition:
            "box-shadow 0.2s ease, transform 0.2s cubic-bezier(0.22, 1, 0.36, 1)",
        }}
      >
        <ProductIcon
          productId={product.id}
          size={52}
          color={owned ? INK : INK_REST}
        />
      </div>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 3,
          minWidth: 0,
          flex: 1,
        }}
      >
        <span
          style={{
            fontSize: 22,
            fontWeight: 500,
            letterSpacing: "-0.01em",
            lineHeight: 1.15,
            color: owned ? INK : INK_REST,
          }}
        >
          {name}
        </span>
        <span
          style={{
            fontSize: 14,
            color: INK_MUTED,
            lineHeight: 1.35,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {tagline}
        </span>
        <span
          style={{
            fontSize: 14,
            color: owned ? INK_MUTED : INK_REST,
            lineHeight: 1.35,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {owned ? summary : `[${summary}]`}
        </span>
      </div>
    </motion.div>
  );
};

export default ProductCardMinimal;
