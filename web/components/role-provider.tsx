"use client";
import { createContext, useContext, useMemo, useState } from "react";
export type DemoRole = "employee" | "finance_reviewer";
const RoleContext = createContext<{ role: DemoRole; setRole: (role: DemoRole) => void }>({ role: "employee", setRole: () => undefined });
export function RoleProvider({ children }: { children: React.ReactNode }) { const [role, setRole] = useState<DemoRole>("employee"); const value = useMemo(() => ({ role, setRole }), [role]); return <RoleContext.Provider value={value}>{children}</RoleContext.Provider>; }
export const useRole = () => useContext(RoleContext);
