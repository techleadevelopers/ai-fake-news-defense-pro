import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";
import { 
  ShieldAlert, 
  LayoutDashboard, 
  ScanEye, 
  Bot, 
  History, 
  Settings, 
  Network,
  LogOut,
  Puzzle,
  Code2,
  CreditCard
} from "lucide-react";

const navigation = [
  { name: 'Painel', href: '/', icon: LayoutDashboard },
  { name: 'Scanner', href: '/content', icon: ScanEye },
  { name: 'Modelos IA', href: '/compliance', icon: Bot },
  { name: 'Mapa Viral', href: '/models', icon: Network },
  { name: 'Integrações', href: '/integrations', icon: Puzzle },
  { name: 'API Dev', href: '/developer', icon: Code2 },
  { name: 'Planos', href: '/billing', icon: CreditCard },
  { name: 'Ajustes', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const [location] = useLocation();

  return (
    <div className="flex h-screen flex-col bg-sidebar text-sidebar-foreground border-r border-sidebar-border w-64 flex-shrink-0">
      <div className="flex h-16 items-center px-6 border-b border-sidebar-border">
        <ShieldAlert className="h-6 w-6 text-primary mr-2" />
        <div>
          <span className="font-bold text-lg tracking-tight block leading-none">Risk Guardian</span>
          <span className="text-[10px] text-muted-foreground font-mono uppercase tracking-wider">Defesa Anti-Fake</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-4">
        <nav className="px-3 space-y-1">
          {navigation.map((item) => {
            const isActive = location === item.href;
            return (
              <Link 
                key={item.name} 
                href={item.href}
                className={cn(
                  "group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
                )}
              >
                <item.icon
                  className={cn(
                    "mr-3 h-5 w-5 flex-shrink-0",
                    isActive ? "text-primary" : "text-sidebar-foreground/50 group-hover:text-sidebar-foreground"
                  )}
                />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="border-t border-sidebar-border p-4">
        <div className="flex items-center">
          <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold text-xs">
            OP
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium">Central Ops</p>
            <p className="text-xs text-sidebar-foreground/50">Analista Nvl 2</p>
          </div>
          <button className="ml-auto text-sidebar-foreground/50 hover:text-sidebar-foreground">
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
