import { Layout } from "@/components/layout/Layout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Globe, Bot, Mic2, Video, Eye, BrainCircuit } from "lucide-react";

const aiModels = [
  {
    id: "MOD-TXT-001",
    name: "Detector de Alucinação LLM v4",
    description: "Detecta padrões de texto típicos de desinformação gerada por GPT-4, Claude e Llama.",
    accuracy: "99.2%",
    type: "Análise de Texto",
    status: true,
    icon: BrainCircuit
  },
  {
    id: "MOD-VID-002",
    name: "Visão Deepfake (Lip-Sync)",
    description: "Analisa incompatibilidade fonema-visema para detectar cabeças falantes geradas por IA.",
    accuracy: "98.5%",
    type: "Forense de Vídeo",
    status: true,
    icon: Video
  },
  {
    id: "MOD-AUD-001",
    name: "Sentinela de Clonagem de Voz",
    description: "Identifica artefatos de áudio sintético e falta de padrões naturais de respiração.",
    accuracy: "97.8%",
    type: "Forense de Áudio",
    status: true,
    icon: Mic2
  },
  {
    id: "MOD-IMG-003",
    name: "Scanner de Artefatos de Difusão",
    description: "Detecta marcas d'água invisíveis e inconsistências de pixels do Midjourney/DALL-E.",
    accuracy: "96.4%",
    type: "Forense de Imagem",
    status: true,
    icon: Eye
  },
  {
    id: "MOD-BOT-005",
    name: "Análise de Cluster de Botnet Social",
    description: "Identifica comportamento inautêntico coordenado (CIB) em plataformas sociais.",
    accuracy: "94.1%",
    type: "Análise de Rede",
    status: false,
    icon: Bot
  }
];

export default function Compliance() {
  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Modelos de Detecção de IA</h1>
            <p className="text-muted-foreground">Configure as redes neurais ativas usadas para classificação de fake news.</p>
          </div>
          <button className="flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors">
            <BrainCircuit className="h-4 w-4" /> Treinar Novo Modelo
          </button>
        </div>

        <div className="grid gap-6">
          {aiModels.map((model) => (
            <Card key={model.id} className="transition-all hover:shadow-md border-l-4 border-l-transparent hover:border-l-primary group">
              <CardContent className="p-6 flex items-start justify-between">
                <div className="flex gap-4">
                  <div className="mt-1 h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    <model.icon className="h-6 w-6" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-lg">{model.name}</h3>
                      <Badge variant="outline" className="font-mono text-xs">
                        {model.id}
                      </Badge>
                      <Badge className="bg-green-100 text-green-700 border-green-200 hover:bg-green-200">
                        Precisão: {model.accuracy}
                      </Badge>
                    </div>
                    <p className="text-muted-foreground max-w-2xl">
                      {model.description}
                    </p>
                    
                    <div className="flex items-center gap-4 pt-3 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1.5 font-medium">
                        {model.type}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right mr-4">
                    <span className="block text-sm font-medium">Status do Modelo</span>
                    <span className={model.status ? "text-xs text-green-600 font-medium" : "text-xs text-muted-foreground"}>
                      {model.status ? "Ativo" : "Offline"}
                    </span>
                  </div>
                  <Switch checked={model.status} />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </Layout>
  );
}
