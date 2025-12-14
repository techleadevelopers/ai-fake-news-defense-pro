import { Layout } from "@/components/layout/Layout";
import { Card, CardContent } from "@/components/ui/card";
import { mockAuditLogs } from "@/lib/mockData";
import { Shield, Fingerprint, Lock } from "lucide-react";

export default function AuditLogs() {
  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Registro de Auditoria</h1>
            <p className="text-muted-foreground">Registro imutável de todas as decisões do sistema.</p>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground bg-muted/50 px-3 py-1 rounded-md border border-border">
            <Lock className="h-3 w-3" />
            <span>Integridade do Registro: Verificada</span>
          </div>
        </div>

        <div className="relative border-l border-border ml-3 space-y-8 pb-12">
          {mockAuditLogs.map((log) => (
            <div key={log.id} className="relative pl-8">
              <span className="absolute -left-1.5 top-1.5 h-3 w-3 rounded-full bg-primary ring-4 ring-background" />
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm font-bold text-primary">{log.timestamp}</span>
                  <span className="h-px w-8 bg-border"></span>
                  <span className="text-sm font-medium text-muted-foreground">{log.action}</span>
                </div>
                
                <Card className="max-w-3xl">
                  <CardContent className="p-4 grid gap-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Usuário / Agente</span>
                        <div className="font-mono text-sm mt-1">{log.user}</div>
                      </div>
                      <div>
                        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">ID Alvo</span>
                        <div className="font-mono text-sm mt-1">{log.targetId}</div>
                      </div>
                    </div>
                    
                    <div>
                      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Detalhes</span>
                      <div className="text-sm mt-1">{log.details}</div>
                    </div>

                    <div className="bg-muted/50 p-2 rounded border border-border flex items-center gap-2">
                      <Fingerprint className="h-4 w-4 text-muted-foreground" />
                      <code className="text-xs text-muted-foreground flex-1 break-all">
                        HASH: {log.hash}
                      </code>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
