/**
 * Unit tests for the AI listing API helpers (B1 description, B2 category, C1 similar).
 */

import {
  generateListingDescription,
  getSimilarListings,
  getFlaggedListings,
  approveFlaggedListing,
  adminRemoveListing,
} from "../api";
import { setAuthToken } from "../auth";
import { mockFetch, mockFetchError, cleanupMocks } from "@/test-utils";

describe("AI listing api helpers", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  afterEach(() => {
    cleanupMocks();
  });

  describe("generateListingDescription", () => {
    it("returns the generated description", async () => {
      setAuthToken("test-token");
      mockFetch({ description: "A sturdy oak desk." });

      const result = await generateListingDescription({ title: "Oak desk", category: "furniture" });

      expect(result.description).toBe("A sturdy oak desk.");
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/ai/generate-description"),
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({ Authorization: "Bearer test-token" }),
        }),
      );
    });

    it("throws when not authenticated", async () => {
      await expect(generateListingDescription({ title: "x" })).rejects.toThrow(
        "Authentication required",
      );
    });

    it("surfaces the backend error detail", async () => {
      setAuthToken("test-token");
      mockFetchError("AI features are disabled", 503);

      await expect(generateListingDescription({ title: "x" })).rejects.toThrow(
        "AI features are disabled",
      );
    });
  });

  describe("getSimilarListings", () => {
    it("returns the similar listings with a limit query param", async () => {
      mockFetch([{ id: "l1", title: "Desk" }]);

      const result = await getSimilarListings("listing-1", 6);

      expect(result).toHaveLength(1);
      expect(result[0].id).toBe("l1");
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/listings/listing-1/similar?limit=6"),
      );
    });

    it("throws on a non-array response", async () => {
      mockFetch({ not: "an array" });

      await expect(getSimilarListings("listing-1")).rejects.toThrow("Invalid response format");
    });
  });

  describe("admin moderation", () => {
    it("getFlaggedListings returns the review queue", async () => {
      setAuthToken("test-token");
      mockFetch({
        items: [{ action_id: "a1", reason: "scam", flagged_at: "now", listing: { id: "l1" } }],
        count: 1,
      });

      const result = await getFlaggedListings();

      expect(result.count).toBe(1);
      expect(result.items[0].listing.id).toBe("l1");
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/admin/flagged-listings"),
        expect.objectContaining({
          headers: expect.objectContaining({ Authorization: "Bearer test-token" }),
        }),
      );
    });

    it("approveFlaggedListing posts to the approve endpoint", async () => {
      setAuthToken("test-token");
      mockFetch({ listing_id: "l1", status: "approved" });

      await approveFlaggedListing("l1");

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/admin/listings/l1/approve"),
        expect.objectContaining({ method: "POST" }),
      );
    });

    it("adminRemoveListing surfaces the backend error detail", async () => {
      setAuthToken("test-token");
      mockFetchError("Cannot remove a listing posted by an admin", 403);

      await expect(adminRemoveListing("l1", "spam")).rejects.toThrow(
        "Cannot remove a listing posted by an admin",
      );
    });

    it("getFlaggedListings throws when not authenticated", async () => {
      await expect(getFlaggedListings()).rejects.toThrow("Authentication required");
    });
  });
});
