import { Layout } from "@/components/layout/Layout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Search, Plus, CheckCircle2, ArrowRight } from "lucide-react";

const integrations = [
  {
    id: "instagram",
    name: "Instagram",
    category: "Social",
    description: "Analisa imagens e reels em busca de conteúdo manipulado e deepfakes automaticamente.",
    status: "Conectado",
    icon: "📸"
  },
  {
    id: "twitter",
    name: "X (Twitter)",
    category: "Social",
    description: "Monitoramento em tempo real para clusters de bots e desinformação em alta.",
    status: "Disponível",
    icon: "✖️"
  },
  {
    id: "tiktok",
    name: "TikTok",
    category: "Vídeo",
    description: "Análise de vídeo quadro a quadro para trocas de rosto e sobreposição de áudio sintético.",
    status: "Disponível",
    icon: "🎵"
  },
  {
    id: "wordpress",
    name: "WordPress",
    category: "CMS",
    description: "Plugin para verificar rascunhos de artigos antes da publicação, prevenindo fake news acidentais.",
    status: "Em Breve",
    icon: "📝"
  },
  {
    id: "slack",
    name: "Slack",
    category: "Notificações",
    description: "Receba alertas críticos de segurança diretamente no seu canal de Ops.",
    status: "Conectado",
    icon: "💬"
  },
  {
    id: "salesforce",
    name: "Salesforce",
    category: "CRM",
    description: "Enriqueça perfis de clientes com pontuações de risco e dados de verificação social.",
    status: "Disponível",
    icon: "☁️"
  }
];

export default function Integrations() {
  return (
    <Layout>
      <div className="space-y-6 max-w-6xl mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Mercado de Integrações</h1>
            <p className="text-muted-foreground">Conecte o Risk Guardian à sua stack existente.</p>
          </div>
          <div className="relative w-[300px]">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input placeholder="Buscar integrações..." className="pl-9" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {integrations.map((item) => (
            <Card key={item.id} className="flex flex-col hover:border-primary/50 transition-colors group">
              <CardHeader>
                <div className="flex items-start justify-between">
                   <div className="h-12 w-12 rounded-lg bg-muted flex items-center justify-center text-2xl group-hover:scale-110 transition-transform duration-300">
                     {item.icon}
                   </div>
                   {item.status === 'Conectado' ? (
                     <Badge className="bg-green-500/10 text-green-600 hover:bg-green-500/20 border-green-500/20">
                       <CheckCircle2 className="mr-1 h-3 w-3" /> Instalado
                     </Badge>
                   ) : item.status === 'Em Breve' ? (
                     <Badge variant="outline" className="text-muted-foreground">Lista de Espera</Badge>
                   ) : (
                     <Badge variant="secondary">Disponível</Badge>
                   )}
                </div>
                <CardTitle className="mt-4">{item.name}</CardTitle>
                <CardDescription className="line-clamp-2 min-h-[40px]">
                  {item.description}
                </CardDescription>
              </CardHeader>
              <CardFooter className="mt-auto pt-0">
                <Button 
                  variant={item.status === 'Conectado' ? "outline" : "default"} 
                  className="w-full"
                  disabled={item.status === 'Em Breve'}
                >
                  {item.status === 'Conectado' ? 'Configurar' : item.status === 'Em Breve' ? 'Notifique-me' : 'Conectar'}
                </Button>
              </CardFooter>
            </Card>
          ))}
          
          <Card className="flex flex-col items-center justify-center border-dashed p-6 text-center hover:bg-muted/50 transition-colors cursor-pointer min-h-[250px]">
            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4">
              <Plus className="h-6 w-6" />
            </div>
            <h3 className="font-semibold">Crie o seu</h3>
            <p className="text-sm text-muted-foreground mt-2 mb-4 max-w-[200px]">
              Use nossa API de Desenvolvedor para criar conectores personalizados para suas ferramentas proprietárias.
            </p>
            <Button variant="link" className="text-primary gap-1">
              Ver Documentação <ArrowRight className="h-4 w-4" />
            </Button>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
