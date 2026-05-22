/* eslint-disable @next/next/no-img-element */
"use client";

import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Minus, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { useState } from "react";

const productData = {
  name: "Man Black Cotton T-Shirt",
  description:
    "A comfortable and durable cotton t-shirt for men. Gives you a perfect fit and a great look for every occasion.",
  category: "Clothing",
  rating: 4.9,
  originalPrice: 25.4,
  discount: 6,
  currency: "$",
  images: [
    "https://images.unsplash.com/photo-1502389614483-e475fc34407e?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&q=80&w=774",
    "https://images.unsplash.com/photo-1618453292459-53424b66bb6a?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&q=80&w=928",
    "https://images.unsplash.com/photo-1618453292507-4959ece6429e?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&q=80&w=928",
    "https://images.unsplash.com/photo-1617984102437-a4aa52284d00?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&q=80&w=774",
  ],
  sizes: ["S", "M", "L", "XL", "XXL"],
  stockMessage: "Last 1 left - make it yours!",
};

export function ProductDetailOne() {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [selectedSize, setSelectedSize] = useState("S");
  const [quantity, setQuantity] = useState(1);

  const nextImage = () => {
    setCurrentImageIndex((prev) => (prev + 1) % productData.images.length);
  };

  const prevImage = () => {
    setCurrentImageIndex(
      (prev) => (prev - 1 + productData.images.length) % productData.images.length,
    );
  };

  const incrementQuantity = () => setQuantity((prev) => prev + 1);
  const decrementQuantity = () => setQuantity((prev) => Math.max(1, prev - 1));

  return (
    <div className="not-prose mx-auto w-full max-w-6xl p-6">
      <div className="grid grid-cols-1 gap-12 lg:grid-cols-2">
        {/* Image Section */}
        <div className="flex gap-2">
          <div className="flex w-28 flex-col gap-2">
            {productData.images.map((image, index) => (
              <button
                key={index}
                onClick={() => setCurrentImageIndex(index)}
                className={cn(
                  "aspect-square overflow-hidden rounded-lg border-2 bg-gray-100 transition-colors",
                  currentImageIndex === index ? "border-gray-900" : "border-transparent",
                )}
              >
                <img
                  src={image}
                  alt={`${productData.name} ${index + 1}`}
                  className="h-full w-full object-cover"
                />
              </button>
            ))}
          </div>

          <div className="relative aspect-[3/4] flex-1 overflow-hidden rounded-lg bg-gray-100">
            <img
              src={productData.images[currentImageIndex]}
              alt={productData.name}
              className="h-full w-full object-cover"
            />

            {/* Navigation Arrows */}
            <Button
              variant="outline"
              size="icon"
              className="absolute top-1/2 left-4 -translate-y-1/2 rounded-full bg-white/80 backdrop-blur-sm"
              onClick={prevImage}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="absolute top-1/2 right-4 -translate-y-1/2 rounded-full bg-white/80 backdrop-blur-sm"
              onClick={nextImage}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Product Info Section */}
        <div className="space-y-6">
          <div>
            <a href="#" className="mb-2 inline-block text-muted-foreground hover:text-gray-900">
              {productData.category}
            </a>
            <h1 className="text-3xl font-bold">{productData.name}</h1>
            <p className="text-muted-foreground">{productData.description}</p>
          </div>

          <div className="flex items-end gap-2">
            <p className="text-3xl font-bold">
              {productData.currency}
              {productData.originalPrice - productData.discount}
            </p>
            <p className="text-2xl font-medium text-gray-400 line-through">
              {productData.currency}
              {productData.originalPrice}
            </p>
          </div>

          <div>
            <h3 className="mb-2 text-sm font-medium">Available Sizes:</h3>
            <div className="flex gap-2">
              {productData.sizes.map((size) => (
                <Button
                  key={size}
                  variant={selectedSize === size ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedSize(size)}
                >
                  {size}
                </Button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center rounded-lg border border-gray-300">
              <Button
                variant="ghost"
                size="icon"
                className="h-10 w-10 rounded-lg hover:bg-gray-100"
                onClick={decrementQuantity}
              >
                <Minus className="h-4 w-4" />
              </Button>
              <span className="w-12 text-center font-medium">{quantity}</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-10 w-10 rounded-lg hover:bg-gray-100"
                onClick={incrementQuantity}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <Button size="lg">Add to cart</Button>
          </div>
        </div>
      </div>
    </div>
  );
}
