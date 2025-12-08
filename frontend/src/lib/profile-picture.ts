import { STATIC_BASE_URL } from "./constants";

/**
 * Build full URL for profile picture with cache busting.
 *
 * Uses the profile's updated_at timestamp to create a unique cache-busting
 * parameter, ensuring browsers fetch fresh images when the profile changes.
 *
 * @param path - Profile picture path (relative or absolute URL)
 * @param updatedAt - ISO timestamp from profile.updated_at field
 * @returns Full URL with cache-busting parameter, or null if no path
 *
 * @example
 * ```ts
 * const url = getProfilePictureUrl(profile.profile_picture_url, profile.updated_at);
 * // => "http://127.0.0.1:8000/uploads/profiles/abc123/profile.jpg?v=1702321695575"
 * ```
 */
export function getProfilePictureUrl(
  path: string | null | undefined,
  updatedAt: string | null | undefined
): string | null {
  if (!path) return null;

  const cacheBuster = updatedAt ? `?v=${new Date(updatedAt).getTime()}` : `?v=${Date.now()}`;

  if (path.startsWith("http://") || path.startsWith("https://")) {
    return `${path}${cacheBuster}`;
  }

  return `${STATIC_BASE_URL}${path}${cacheBuster}`;
}
