/**
 * Unit tests for profile picture utilities
 */

import { getProfilePictureUrl } from "../profile-picture";
import { STATIC_BASE_URL } from "../constants";

describe("profile-picture.ts", () => {
  const FALLBACK_BASE_URL = STATIC_BASE_URL;

  describe("getProfilePictureUrl", () => {
    it("should return null if path is null", () => {
      expect(getProfilePictureUrl(null, "2024-01-01T00:00:00Z")).toBeNull();
    });

    it("should return null if path is undefined", () => {
      expect(getProfilePictureUrl(undefined, "2024-01-01T00:00:00Z")).toBeNull();
    });

    it("should return null if path is empty string", () => {
      expect(getProfilePictureUrl("", "2024-01-01T00:00:00Z")).toBeNull();
    });

    it("should add cache buster to relative path", () => {
      const updatedAt = "2024-01-01T00:00:00Z";
      const expectedTimestamp = new Date(updatedAt).getTime();
      const result = getProfilePictureUrl("/uploads/profiles/123/avatar.jpg", updatedAt);

      expect(result).toBe(
        `${FALLBACK_BASE_URL}/uploads/profiles/123/avatar.jpg?v=${expectedTimestamp}`
      );
    });

    it("should add cache buster to absolute HTTP URL", () => {
      const updatedAt = "2024-01-01T00:00:00Z";
      const expectedTimestamp = new Date(updatedAt).getTime();
      const absoluteUrl = "http://example.com/avatar.jpg";
      const result = getProfilePictureUrl(absoluteUrl, updatedAt);

      expect(result).toBe(`${absoluteUrl}?v=${expectedTimestamp}`);
    });

    it("should add cache buster to absolute HTTPS URL", () => {
      const updatedAt = "2024-01-01T00:00:00Z";
      const expectedTimestamp = new Date(updatedAt).getTime();
      const absoluteUrl = "https://example.com/avatar.jpg";
      const result = getProfilePictureUrl(absoluteUrl, updatedAt);

      expect(result).toBe(`${absoluteUrl}?v=${expectedTimestamp}`);
    });

    it("should use current timestamp if updatedAt is null", () => {
      const beforeTime = Date.now();
      const result = getProfilePictureUrl("/uploads/avatar.jpg", null);
      const afterTime = Date.now();

      expect(result).toMatch(
        new RegExp(`^${FALLBACK_BASE_URL.replace(/\//g, "\\/")}\/uploads\/avatar\\.jpg\\?v=\\d+$`)
      );

      const timestamp = parseInt(result!.split("?v=")[1]);
      expect(timestamp).toBeGreaterThanOrEqual(beforeTime);
      expect(timestamp).toBeLessThanOrEqual(afterTime);
    });

    it("should use current timestamp if updatedAt is undefined", () => {
      const beforeTime = Date.now();
      const result = getProfilePictureUrl("/uploads/avatar.jpg", undefined);
      const afterTime = Date.now();

      expect(result).toMatch(
        new RegExp(`^${FALLBACK_BASE_URL.replace(/\//g, "\\/")}\/uploads\/avatar\\.jpg\\?v=\\d+$`)
      );

      const timestamp = parseInt(result!.split("?v=")[1]);
      expect(timestamp).toBeGreaterThanOrEqual(beforeTime);
      expect(timestamp).toBeLessThanOrEqual(afterTime);
    });

    it("should handle different date formats", () => {
      const updatedAt = "2024-06-15T14:30:45.123Z";
      const expectedTimestamp = new Date(updatedAt).getTime();
      const result = getProfilePictureUrl("/uploads/profile.jpg", updatedAt);

      expect(result).toBe(`${FALLBACK_BASE_URL}/uploads/profile.jpg?v=${expectedTimestamp}`);
    });

    it("should preserve path structure", () => {
      const path = "/uploads/profiles/user-123/avatar-large.png";
      const updatedAt = "2024-01-01T00:00:00Z";
      const result = getProfilePictureUrl(path, updatedAt);

      expect(result).toContain(path);
      expect(result.startsWith(FALLBACK_BASE_URL)).toBe(true);
    });
  });
});
