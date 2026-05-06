export type ProductId = "helios" | "janus" | "lethe" | "astralis";

export interface Product {
  id: ProductId;
  name: string;
  tagline: string;
  summary: string;
  description: string;
  href: string;
  owned: boolean;
}

export const PRODUCTS: Product[] = [
  {
    id: "helios",
    name: "Helios",
    tagline: "Discovery & Inventory",
    summary: "91% Coverage  •  +4% Classified",
    description:
      "Surfaces systems, datasets, and data categories across your estate.",
    href: "/poc/grid-motion/helios",
    owned: true,
  },
  {
    id: "janus",
    name: "Janus",
    tagline: "Consent",
    summary: "94% Pass  •  12 No-consent",
    description:
      "Vendor, framework, and notice alignment across every surface.",
    href: "/poc/grid-motion/janus",
    owned: true,
  },
  {
    id: "lethe",
    name: "Lethe",
    tagline: "Privacy Requests",
    summary: "Not configured",
    description: "DSR queues, SLA health, and integration connection state.",
    href: "/poc/grid-motion/lethe",
    owned: false,
  },
  {
    id: "astralis",
    name: "Astralis",
    tagline: "AI Governance",
    summary: "3 Critical  •  5 PIAs open",
    description:
      "PIAs, policy enforcement, and AI-system readiness across your stack.",
    href: "/poc/grid-motion/astralis",
    owned: true,
  },
];
