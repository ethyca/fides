import { useLiveRegion } from "../lib/providers/live-region-context";

export const LiveRegion = () => {
  const { message } = useLiveRegion();
  return (
    <div
      role="status"
      aria-live="polite"
      aria-relevant="additions"
      className="fides-sr-only"
      id="fides-overlay-live-region"
    >
      {message}
    </div>
  );
};
