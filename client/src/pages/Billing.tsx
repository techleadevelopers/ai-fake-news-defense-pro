import { Layout } from "@/components/layout/Layout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, Zap, Building2, Globe, ShieldCheck } from "lucide-react";

const plans = [
  {
    name: "Inicial",
    price: "$999",
    period: "/mês",
    description: "Para startups e pequenos veículos de mídia.",
    features: [
      "100.000 Chamadas de API / mês",
      "Modelos de Detecção Padrão",
      "Suporte por Email",
      "3 Membros na Equipe",
      "Retenção de Auditoria de 7 Dias"
    ],
    cta: "Downgrade",
    current: false,
    popular: false
  },
  {
    name: "Crescimento",
    price: "$4.999",
    period: "/mês",
    description: "Para plataformas em escala e agências de notícias regionais.",
    features: [
      "2.000.000 Chamadas de API / mês",
      "Detecção Avançada de Deepfake",
      "Suporte Prioritário no Slack",
      "20 Membros na Equipe",
      "Retenção de Auditoria de 90 Dias",
      "Gerente de Conta Dedicado"
    ],
    cta: "Plano Atual",
    current: true,
    popular: true
  },
  {
    name: "Empresarial",
    price: "Custom",
    period: "",
    description: "Para governos nacionais e redes sociais globais.",
    features: [
      "Chamadas de API Ilimitadas",
      "Treinamento de Modelo Personalizado",
      "Equipe de Resposta Dedicada 24/7",
      "Opção de Implantação On-Premise",
      "Retenção de Auditoria Infinita",
      "Garantia de SLA 99.999%"
    ],
    cta: "Contatar Vendas",
    current: false,
    popular: false
  }
];

export default function Billing() {
  return (
    <Layout>
      <div className="space-y-8 max-w-6xl mx-auto">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Assinatura e Cobrança</h1>
          <p className="text-muted-foreground">Gerencie seu plano, limites de uso e métodos de pagamento.</p>
        </div>

        {/* Usage Stats */}
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="p-6 flex items-center justify-between">
             <div className="space-y-1">
               <h3 className="font-semibold text-lg flex items-center gap-2">
                 <Zap className="h-4 w-4 text-primary" />
                 Uso Atual
               </h3>
               <p className="text-sm text-muted-foreground">Ciclo de cobrança reinicia em 12 dias</p>
             </div>
             <div className="flex-1 max-w-md mx-8 space-y-2">
               <div className="flex justify-between text-sm">
                 <span>1.2M / 2.0M Requisições</span>
                 <span className="font-bold text-primary">60%</span>
               </div>
               <div className="h-2 w-full bg-background rounded-full overflow-hidden border">
                 <div className="h-full bg-primary w-[60%] rounded-full" />
               </div>
             </div>
             <Button variant="outline">Ver Faturas</Button>
          </CardContent>
        </Card>

        {/* Plans Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan) => (
            <Card 
              key={plan.name} 
              className={`flex flex-col relative ${plan.popular ? 'border-primary shadow-lg scale-105 z-10' : 'border-border'}`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-xs font-bold px-3 py-1 rounded-full">
                  MAIS POPULAR
                </div>
              )}
              <CardHeader>
                <CardTitle className="text-xl">{plan.name}</CardTitle>
                <CardDescription>{plan.description}</CardDescription>
                <div className="mt-4">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  <span className="text-muted-foreground">{plan.period}</span>
                </div>
              </CardHeader>
              <CardContent className="flex-1">
                <ul className="space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm">
                      <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                      <span className="text-muted-foreground">{feature}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter>
                <Button 
                  className="w-full" 
                  variant={plan.current ? "outline" : "default"}
                  disabled={plan.current}
                >
                  {plan.cta}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>

        {/* Enterprise Trusted By */}
        <div className="pt-8 border-t">
          <p className="text-center text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-6">
            Confiado por Líderes Globais
          </p>
          <div className="flex justify-center gap-12 opacity-50 grayscale hover:grayscale-0 transition-all duration-500">
            <div className="flex items-center gap-2 font-bold text-xl"><Globe className="h-6 w-6" /> GovTech</div>
            <div className="flex items-center gap-2 font-bold text-xl"><ShieldCheck className="h-6 w-6" /> SecureNet</div>
            <div className="flex items-center gap-2 font-bold text-xl"><Building2 className="h-6 w-6" /> CorpMedia</div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
