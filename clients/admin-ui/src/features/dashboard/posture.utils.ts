import { DiffDirection, PostureResponse } from "./types";

interface PostureDiffText {
  direction: DiffDirection;
  points: number;
  text: string;
}

/**
 * Mirrors the first sentence of fidesplus `_posture_annotation` so the
 * frontend can render a short version without parsing the full string.
 * The backend's `diff_percent` is actually the raw point delta against the
 * previous day's snapshot (see dashboard_service.get_posture).
 */
export const getPostureDiffText = (
  posture: PostureResponse | undefined,
): PostureDiffText | null => {
  if (!posture) {
    return null;
  }
  const points = Math.abs(posture.diff_percent);
  if (posture.diff_direction === DiffDirection.UP) {
    return {
      direction: DiffDirection.UP,
      points,
      text: `Your score increased by ${points.toFixed(1)} points over the last week`,
    };
  }
  if (posture.diff_direction === DiffDirection.DOWN) {
    return {
      direction: DiffDirection.DOWN,
      points,
      text: `Your score decreased by ${points.toFixed(1)} points over the last week`,
    };
  }
  return null;
};
