import { motion } from "framer-motion";
import { useState } from "react";

import { buildBoxShadow, GLASS_BG_NEUTRAL, GLASS_TRANSITION } from "./glass";
import { VizBlock, type VizBlockProps } from "./MetricViz";
import ProductIcon from "./ProductIcon";
import type { Product, ProductId } from "./products";

const INK = "#2b2e35";
const INK_MUTED = "rgba(43,46,53,0.55)";

interface ProductCardMetricsProps {
  product: Product;
  onSelect: (id: Product["id"]) => void;
  index?: number;
}

const VIZ_BY_PRODUCT: Record<ProductId, VizBlockProps[]> = {
  helios: [
    {
      kind: "hbar",
      label: "Managed",
      caption: "91%",
      fraction: 0.91,
      tone: "neutral",
    },
    {
      kind: "spark",
      label: "Classification",
      caption: "+4",
      points: [60, 62, 63, 64, 66, 67, 68, 69, 70, 72, 72, 73],
      tone: "neutral",
    },
  ],
  janus: [
    {
      kind: "spark",
      label: "Monitoring pass",
      caption: "94%",
      points: [88, 91, 90, 92, 93, 91, 94, 95, 93, 94, 94, 94],
      tone: "neutral",
    },
    {
      kind: "dots",
      label: "No-consent",
      caption: "12",
      filled: 12,
      total: 16,
      tone: "warn",
      captionTone: "warn",
    },
  ],
  lethe: [],
  astralis: [
    {
      kind: "dots",
      label: "Critical",
      caption: "3",
      filled: 3,
      total: 12,
      tone: "critical",
      captionTone: "critical",
    },
    {
      kind: "spark",
      label: "PIA throughput",
      caption: "5 open",
      points: [3, 4, 4, 5, 6, 6, 5, 5, 6, 5, 5, 5],
      tone: "neutral",
    },
  ],
};

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

const CtaButton = ({ hover }: { hover: boolean }) => (
  <span
    style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 6,
      fontSize: 12,
      fontWeight: 500,
      letterSpacing: "0.01em",
      color: INK,
      borderBottom: `1px solid ${hover ? INK : "rgba(43,46,53,0.25)"}`,
      paddingBottom: 1,
      transition: "border-color 0.18s ease",
    }}
  >
    Open dashboard
    <motion.span
      animate={{ x: hover ? 3 : 0 }}
      transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
      style={{ fontSize: 14, lineHeight: 1, display: "inline-block" }}
    >
      →
    </motion.span>
  </span>
);

const ProductCardMetrics = ({
  product,
  onSelect,
  index = 0,
}: ProductCardMetricsProps) => {
  const [hover, setHover] = useState(false);
  const { name, tagline, owned, id } = product;
  const interactive = owned;
  const vizs = owned ? VIZ_BY_PRODUCT[id] : [];

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
        flexDirection: "column",
        justifyContent: "space-between",
        gap: 12,
        padding: 16,
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
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      {!owned && <NotInPlanBadge />}

      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <ProductIcon productId={product.id} size={28} />
        <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
          <span
            style={{
              fontSize: 17,
              fontWeight: 500,
              letterSpacing: "-0.01em",
              lineHeight: 1.1,
            }}
          >
            {name}
          </span>
          <span style={{ fontSize: 11, color: INK_MUTED }}>{tagline}</span>
        </div>
      </div>

      {vizs.length > 0 && (
        <div style={{ display: "flex", gap: 20, alignItems: "stretch" }}>
          {vizs.map((v) => (
            <VizBlock key={v.label} {...v} />
          ))}
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        {owned ? (
          <CtaButton hover={hover} />
        ) : (
          <span
            style={{
              fontSize: 12,
              color: INK_MUTED,
              fontWeight: 500,
              letterSpacing: "0.02em",
            }}
          >
            Not in your plan
          </span>
        )}
      </div>
    </motion.button>
  );
};

export default ProductCardMetrics;
