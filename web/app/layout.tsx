import type { Metadata } from "next";
import { AppShell } from "@/components/app-shell";
import { RoleProvider } from "@/components/role-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Finance AI Copilot",
  description: "有依据、可复核的财务智能工作台",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        <RoleProvider>
          <AppShell>{children}</AppShell>
        </RoleProvider>
      </body>
    </html>
  );
}
