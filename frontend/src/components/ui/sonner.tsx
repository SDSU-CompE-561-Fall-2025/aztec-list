"use client";

import {
  CircleCheckIcon,
  InfoIcon,
  Loader2Icon,
  OctagonXIcon,
  TriangleAlertIcon,
} from "lucide-react";
import { useTheme } from "next-themes";
import { Toaster as Sonner, type ToasterProps } from "sonner";

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme();

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      icons={{
        success: <CircleCheckIcon className="size-4" />,
        info: <InfoIcon className="size-4" />,
        warning: <TriangleAlertIcon className="size-4" />,
        error: <OctagonXIcon className="size-4" />,
        loading: <Loader2Icon className="size-4 animate-spin" />,
      }}
      toastOptions={{
        style: {
          borderRadius: "8px",
        },
        classNames: {
          success: "!bg-[rgb(20,83,45)] !text-white !border-[rgb(34,197,94)]",
          error: "!bg-[rgb(153,27,27)] !text-white !border-[rgb(220,38,38)]",
          warning: "!bg-[rgb(161,98,7)] !text-white !border-[rgb(251,191,36)]",
          info: "!bg-[rgb(30,64,175)] !text-white !border-[rgb(96,165,250)]",
        },
      }}
      {...props}
    />
  );
};

export { Toaster };
