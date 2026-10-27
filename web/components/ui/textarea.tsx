import * as React from "react";
import { cn } from "@/lib/utils";
export function Textarea({ className, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) { return <textarea className={cn("min-h-24 w-full resize-y rounded-lg border bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:ring-2", className)} {...props} />; }
