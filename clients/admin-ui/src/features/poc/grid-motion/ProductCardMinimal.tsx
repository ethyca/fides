import { motion } from "framer-motion";
import { useState } from "react";

import { buildBoxShadow, GLASS_BG_NEUTRAL, GLASS_TRANSITION } from "./glass";
import ProductIcon from "./ProductIcon";
import type { Product } from "./products";

const INK = "#2b2e35";
const INK_MUTED = "rgba(43,46,53,0.55)";

interface ProductCardMinimalProps {
  product: Product;
  onSelect: (id: Product["id"]) => void;
  index?: number;
}

const NotInPlanBadge = () => (
  <span
    style={{
      position: "absolute",
      top: 14,
      right: 16,
      fontSize: 10,
      letterSpacing: "0.10em",
      textTransform: "uppercase",
      color: INK_MUTED,
    }}
  >
    Not in your plan
  </span>
);

const ProductCardMinimal = ({
  product,
  onSelect,
  index = 0,
}: ProductCardMinimalProps) => {
  const [hover, setHover] = useState(false);
  const { name, tagline, description, owned } = product;
  const interactive = owned;

  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.45,
        ease: [0.22, 1, 0.36, 1],
        delay: index * 0.08,
      }}
      onClick={() => {
        if (interactive) {
          onSelect(product.id);
        }
      }}
      onMouseEnter={() => interactive && setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        position: "relative",
        display: "flex",
        alignItems: "center",
        gap: 20,
        padding: 20,
        border: "none",
        borderRadius: 4,
        background: GLASS_BG_NEUTRAL,
        boxShadow: buildBoxShadow(false, interactive && hover),
        transition: GLASS_TRANSITION,
        textAlign: "left",
        cursor: interactive ? "pointer" : "default",
        opacity: owned ? 1 : 0.55,
        color: INK,
        width: "100%",
        height: "100%",
        maxHeight: 400,
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      {!owned && <NotInPlanBadge />}

      <div
        style={{
          width: 96,
          height: 96,
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "rgba(43,46,53,0.04)",
          boxShadow: "inset 0 0 0 1px rgba(43,46,53,0.06)",
          borderRadius: 4,
        }}
      >
        <ProductIcon productId={product.id} size={64} />
      </div>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 6,
          minWidth: 0,
          flex: 1,
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <span
            style={{
              fontSize: 22,
              fontWeight: 500,
              letterSpacing: "-0.01em",
              lineHeight: 1.1,
            }}
          >
            {name}
          </span>
          <span style={{ fontSize: 12, color: INK_MUTED }}>{tagline}</span>
        </div>
        <p
          style={{
            margin: 0,
            fontSize: 13,
            lineHeight: 1.45,
            color: INK_MUTED,
          }}
        >
          {description}
        </p>
      </div>
    </motion.button>
  );
};

export default ProductCardMinimal;
