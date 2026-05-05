import type { NextPage } from "next";
import { useRouter } from "next/router";

import PageShell from "~/features/poc/grid-motion/PageShell";
import { type ProductId, PRODUCTS } from "~/features/poc/grid-motion/products";

const INK = "#2b2e35";
const INK_MUTED = "rgba(43,46,53,0.55)";

const PillarPage: NextPage = () => {
  const router = useRouter();
  const productId = router.query.product as ProductId | undefined;
  const product = PRODUCTS.find((p) => p.id === productId);

  return (
    <PageShell>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "calc(100vh - 56px)",
          padding: "0 32px",
          textAlign: "center",
          color: INK,
        }}
      >
        <span
          style={{
            fontSize: 11,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: INK_MUTED,
            marginBottom: 12,
          }}
        >
          {product?.tagline ?? "Pillar"}
        </span>
        <h1
          style={{
            fontFamily: "'Eliza', Georgia, serif",
            fontSize: 64,
            fontWeight: 400,
            letterSpacing: "-0.02em",
            margin: 0,
            color: INK,
          }}
        >
          {product?.name ?? "Pillar"}
        </h1>
        <p
          style={{
            marginTop: 16,
            fontSize: 14,
            color: INK_MUTED,
            maxWidth: 480,
            lineHeight: 1.6,
          }}
        >
          Dashboard coming soon.
        </p>
      </div>
    </PageShell>
  );
};

export default PillarPage;
