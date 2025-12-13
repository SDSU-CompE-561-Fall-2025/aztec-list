/**
 * Unit tests for utility functions
 */

import {
  cn,
  formatCategoryLabel,
  formatConditionLabel,
  getConditionColor,
  formatSortLabel,
  formatPrice,
} from "../utils";
import { Category } from "@/types/listing/filters/category";
import { Condition } from "@/types/listing/filters/condition";
import { Sort } from "@/types/listing/filters/sort";

describe("utils.ts", () => {
  describe("cn", () => {
    it("should merge tailwind classes", () => {
      expect(cn("bg-red-500", "text-white")).toBe("bg-red-500 text-white");
    });

    it("should handle conditional classes", () => {
      expect(cn("base-class", true && "conditional-class", false && "hidden-class")).toBe(
        "base-class conditional-class"
      );
    });

    it("should override conflicting classes", () => {
      expect(cn("p-4", "p-8")).toBe("p-8");
    });

    it("should handle arrays and objects", () => {
      expect(cn(["class1", "class2"], { class3: true, class4: false })).toBe(
        "class1 class2 class3"
      );
    });
  });

  describe("formatCategoryLabel", () => {
    it("should format electronics category", () => {
      expect(formatCategoryLabel("electronics" as Category)).toBe("Electronics");
    });

    it("should format textbooks category", () => {
      expect(formatCategoryLabel("textbooks" as Category)).toBe("Textbooks");
    });

    it("should format sports_equipment with space", () => {
      expect(formatCategoryLabel("sports_equipment" as Category)).toBe("Sports Equipment");
    });

    it("should format baby_kids with ampersand", () => {
      expect(formatCategoryLabel("baby_kids" as Category)).toBe("Baby & Kids");
    });

    it("should format other category", () => {
      expect(formatCategoryLabel("other" as Category)).toBe("Other");
    });
  });

  describe("formatConditionLabel", () => {
    it("should format new condition", () => {
      expect(formatConditionLabel("new" as Condition)).toBe("New");
    });

    it("should format like_new condition", () => {
      expect(formatConditionLabel("like_new" as Condition)).toBe("Like New");
    });

    it("should format good condition", () => {
      expect(formatConditionLabel("good" as Condition)).toBe("Good");
    });

    it("should format fair condition", () => {
      expect(formatConditionLabel("fair" as Condition)).toBe("Fair");
    });

    it("should format poor condition", () => {
      expect(formatConditionLabel("poor" as Condition)).toBe("Poor");
    });
  });

  describe("getConditionColor", () => {
    it("should return green for new condition", () => {
      const color = getConditionColor("new" as Condition);
      expect(color).toBe("text-blue-400");
    });

    it("should return emerald for like_new condition", () => {
      const color = getConditionColor("like_new" as Condition);
      expect(color).toBe("text-cyan-400");
    });

    it("should return blue for good condition", () => {
      const color = getConditionColor("good" as Condition);
      expect(color).toBe("text-green-400");
    });

    it("should return amber for fair condition", () => {
      const color = getConditionColor("fair" as Condition);
      expect(color).toBe("text-yellow-400");
    });

    it("should return red for poor condition", () => {
      const color = getConditionColor("poor" as Condition);
      expect(color).toContain("red");
    });
  });

  describe("formatSortLabel", () => {
    it('should format recent as "Most Recent"', () => {
      expect(formatSortLabel("recent" as Sort)).toBe("Most Recent");
    });

    it('should format price_asc as "Price: Low to High"', () => {
      expect(formatSortLabel("price_asc" as Sort)).toBe("Price: Low to High");
    });

    it('should format price_desc as "Price: High to Low"', () => {
      expect(formatSortLabel("price_desc" as Sort)).toBe("Price: High to Low");
    });
  });

  describe("formatPrice", () => {
    it("should format price with dollar sign", () => {
      expect(formatPrice(10.99)).toBe("$10.99");
    });

    it("should format whole numbers", () => {
      expect(formatPrice(100)).toBe("$100.00");
    });

    it("should format zero", () => {
      expect(formatPrice(0)).toBe("$0.00");
    });

    it("should format large numbers with commas", () => {
      expect(formatPrice(1234.56)).toBe("$1,234.56");
    });

    it("should round to 2 decimal places", () => {
      expect(formatPrice(10.999)).toBe("$11.00");
    });
  });
});
