import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

const serif = "'Eliza', Georgia, serif";
const sans = "'Basier Square', system-ui, sans-serif";
const mono = "'Basier Square Mono', ui-monospace, monospace";

const COUNTDOWN_SECONDS = 5;

const CountdownRing = ({
  secondsLeft,
  paused,
}: {
  secondsLeft: number;
  paused: boolean;
}) => {
  const size = 26;
  const strokeWidth = 1;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = secondsLeft / COUNTDOWN_SECONDS;
  const dashOffset = circumference * (1 - progress);

  return (
    <div
      style={{
        position: "relative",
        width: size,
        height: size,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{
          position: "absolute",
          inset: 0,
          transform: "rotate(-90deg)",
        }}
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#c25a2c"
          strokeOpacity={paused ? 1 : 0.25}
          strokeWidth={strokeWidth}
        />
        {!paused && (
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#c25a2c"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            style={{ transition: "stroke-dashoffset 1s linear" }}
          />
        )}
      </svg>
      <span
        style={{
          fontFamily: mono,
          fontWeight: 500,
          fontSize: 11,
          color: "#201c18",
          lineHeight: 1,
        }}
      >
        {secondsLeft}
      </span>
    </div>
  );
};

const PRIORITY_ROWS: {
  label: string;
  status: string;
  tone: "critical" | "due" | "neutral";
}[] = [
  {
    label: "Segment integration outside consent coverage · ~40K users",
    status: "CRITICAL",
    tone: "critical",
  },
  {
    label: "Mobile app SDK consent categories blocked on eng review",
    status: "OVERDUE · 2D",
    tone: "critical",
  },
  {
    label: "HubSpot EU retention policy expired 3 days ago",
    status: "DUE · 2 DAYS",
    tone: "critical",
  },
  {
    label: "Okta DPA renewal awaits your countersignature",
    status: "DUE · 4 DAYS",
    tone: "due",
  },
  {
    label: "BigQuery Analytics — 4 retention questions awaiting input",
    status: "80%",
    tone: "neutral",
  },
];

const toneColor = (tone: "critical" | "due" | "neutral") => {
  if (tone === "critical") {
    return "#b83c27";
  }
  if (tone === "due") {
    return "#c88420";
  }
  return "#8b8175";
};


const OpenContent = ({
  secondsLeft,
  paused,
}: {
  secondsLeft: number;
  paused: boolean;
}) => (
  <div style={{ display: "flex", flexDirection: "column", width: "100%" }}>
    {/* Body */}
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        padding: "64px 72px 52px 72px",
      }}
    >
      <h2
        style={{
          fontFamily: serif,
          fontStyle: "italic",
          fontWeight: 400,
          fontSize: 44,
          lineHeight: 1.15,
          letterSpacing: "-0.88px",
          color: "#201c18",
          margin: "20px 0 24px",
        }}
      >
        Good afternoon, Erin.
      </h2>
      <div
        style={{
          fontFamily: sans,
          fontSize: 14,
          lineHeight: 1.65,
          color: "#544e45",
        }}
      >
        <p style={{ margin: "0 0 1.2em" }}>
          Three privacy assessments were completed overnight, improving your
          overall governance posture by 2 points to 72. The BigQuery Analytics
          assessment is 80% complete with 4 questions awaiting human input on
          data retention policy. The mobile app consent assessment is now
          overdue — it was due Monday and is blocked on engineering review of
          the new SDK&apos;s consent categories.
        </p>
        <p style={{ margin: "0 0 1.2em" }}>
          Two systems flagged for review last week have been resolved: the
          Salesforce classification scan confirmed all 12 new fields, and the
          HubSpot data deletion request was executed across all 3 tables. System
          coverage increased to 91% after the Stripe integration was formally
          mapped last Thursday.
        </p>
        <p style={{ margin: 0 }}>
          One new risk requires attention: the marketing team&apos;s Segment
          integration is sending user data to a region not covered by your
          current consent configuration. This is flagged as critical because it
          affects approximately 40,000 active users. Recommend reviewing consent
          settings for the mobile app and Segment simultaneously, as both
          involve the same regional policy gap.
        </p>
      </div>

      {/* Priority table */}
      <div style={{ marginTop: 32, display: "flex", flexDirection: "column" }}>
        {PRIORITY_ROWS.map((row) => (
          <div
            key={row.label}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 20,
              padding: "5px 0",
              borderBottom: "1px solid rgba(32, 28, 24, 0.08)",
            }}
          >
            <span
              style={{
                flex: 1,
                fontFamily: sans,
                fontSize: 14,
                letterSpacing: "-0.14px",
                color: "#201c18",
                lineHeight: 1.4,
              }}
            >
              {row.label}
            </span>
            <span
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              {row.tone !== "neutral" && (
                <span
                  style={{
                    width: 5,
                    height: 5,
                    borderRadius: "50%",
                    background: toneColor(row.tone),
                    display: "inline-block",
                  }}
                />
              )}
              <span
                style={{
                  fontFamily: mono,
                  fontWeight: 500,
                  fontSize: 10,
                  letterSpacing: "1.2px",
                  color: toneColor(row.tone),
                  whiteSpace: "nowrap",
                }}
              >
                {row.status}
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>

    {/* Footer / input row */}
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "20px 32px 22px",
        borderTop: "1px solid rgba(32, 28, 24, 0.08)",
        gap: 16,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 14,
          minWidth: 0,
          flex: 1,
        }}
      >
        <span style={{ fontFamily: sans, fontSize: 16, color: "#c25a2c" }}>
          ›
        </span>
        <span
          style={{
            fontFamily: sans,
            fontStyle: "italic",
            fontSize: 14,
            color: "#8b8175",
          }}
        >
          Reply to Fides, or type a command…
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <span
          style={{
            fontFamily: mono,
            fontSize: 11,
            letterSpacing: "1.32px",
            color: "#8b8175",
            whiteSpace: "nowrap",
          }}
        >
          ⏎ SEND · ESC COLLAPSE
        </span>
        <CountdownRing secondsLeft={secondsLeft} paused={paused} />
      </div>
    </div>
  </div>
);

const ClosedContent = ({ expanded: _expanded }: { expanded: string | null }) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: 16,
      padding: "18px 24px",
      width: "100%",
    }}
  >
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        minWidth: 0,
        flex: 1,
      }}
    >
      <span style={{ fontFamily: sans, fontSize: 16, color: "#c25a2c" }}>
        ›
      </span>
      <span
        style={{
          fontFamily: sans,
          fontStyle: "italic",
          fontSize: 14,
          color: "#8b8175",
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        Ask Astralis…
      </span>
    </div>
    <span
      style={{
        fontFamily: mono,
        fontSize: 11,
        letterSpacing: "1.32px",
        color: "#8b8175",
        whiteSpace: "nowrap",
      }}
    >
      ⌘K
    </span>
  </div>
);


const ChatPanel = ({ expanded }: { expanded: string | null }) => {
  const [open, setOpen] = useState(true);
  const [secondsLeft, setSecondsLeft] = useState(COUNTDOWN_SECONDS);
  const [hovered, setHovered] = useState(false);
  const hoveredRef = useRef(hovered);
  hoveredRef.current = hovered;
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    const interval = window.setInterval(() => {
      if (hoveredRef.current) {
        return;
      }
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          window.clearInterval(interval);
          setOpen(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => window.clearInterval(interval);
  }, [open]);

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    const handlePointerDown = (e: MouseEvent) => {
      if (!panelRef.current) {
        return;
      }
      if (!panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  const handleReopen = () => {
    if (open) {
      return;
    }
    setSecondsLeft(COUNTDOWN_SECONDS);
    setOpen(true);
  };

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 24,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 12,
        pointerEvents: "none",
        zIndex: 10,
      }}
    >
      <motion.div
        ref={panelRef}
        layout
        initial={false}
        animate={{ width: open ? 800 : 500 }}
        transition={{
          layout: { duration: 0.55, ease: [0.22, 1, 0.36, 1] },
          width: { duration: 0.55, ease: [0.22, 1, 0.36, 1] },
        }}
        style={{
          background: "rgba(255, 255, 255, 0.55)",
          backdropFilter: "blur(14px)",
          WebkitBackdropFilter: "blur(14px)",
          border: "1px solid rgba(32, 28, 24, 0.08)",
          boxShadow: "0 2px 12px rgba(32, 28, 24, 0.04)",
          overflow: "hidden" as const,
          borderRadius: 2,
          cursor: open ? "default" : "pointer",
          pointerEvents: "auto",
        }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        onClick={handleReopen}
      >
        <motion.div layout="position" style={{ width: "100%" }}>
          {open ? (
            <OpenContent secondsLeft={secondsLeft} paused={hovered} />
          ) : (
            <ClosedContent expanded={expanded} />
          )}
        </motion.div>
      </motion.div>
    </div>
  );
};

export default ChatPanel;
