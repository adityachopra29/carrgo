"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";

const navItems = [
  { href: "/", label: "Dashboard", icon: "📊" },
  { href: "/loads", label: "Loads", icon: "📦" },
  { href: "/carriers", label: "Carriers", icon: "🚛" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const router = useRouter();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <aside className="w-64 border-r bg-muted/30 min-h-screen p-4 flex flex-col">
      <div className="mb-8">
        <h1 className="text-xl font-bold">Carrgo</h1>
        <p className="text-xs text-muted-foreground">
          AI Freight Broker Platform
        </p>
      </div>
      <nav className="space-y-1 flex-1">
        {navItems.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted text-muted-foreground hover:text-foreground"
              )}
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>
      {user && (
        <div className="border-t pt-4 mt-4">
          <p className="text-sm font-medium truncate">{user.full_name}</p>
          <p className="text-xs text-muted-foreground truncate mb-3">
            {user.company_name}
          </p>
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={handleLogout}
          >
            Log out
          </Button>
        </div>
      )}
    </aside>
  );
}
