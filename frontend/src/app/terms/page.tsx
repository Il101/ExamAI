import ParticleBackground from "@/components/ParticleBackground";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Terms() {
    return (
        <div className="min-h-screen bg-background relative overflow-hidden">
            <ParticleBackground />
            <div className="container mx-auto px-6 py-20 relative z-10">
                <div className="max-w-3xl mx-auto">
                    <Link href="/">
                        <Button variant="ghost" className="mb-8 pl-0 hover:bg-transparent hover:text-primary transition-colors">
                            <ArrowLeft className="mr-2 h-4 w-4" />
                            Back to Home
                        </Button>
                    </Link>

                    <h1 className="text-4xl font-bold mb-12 bg-gradient-brand bg-clip-text text-transparent inline-block">
                        AGB (Terms of Service)
                    </h1>

                    <div className="space-y-8 text-foreground">
                        <section className="space-y-4">
                            <h2 className="text-xl font-semibold text-primary">§ 1 Altersbeschränkung</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Die Nutzung des Dienstes ist erst ab 14 Jahren gestattet.
                            </p>
                        </section>

                        <section className="space-y-4">
                            <h2 className="text-xl font-semibold text-primary">§ 2 Widerrufsrecht</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Da Sie Verbraucher sind, haben Sie das Recht, diesen Vertrag binnen vierzehn Tagen ohne Angabe von Gründen zu widerrufen. Wir erstatten Ihnen alle Zahlungen zurück.
                            </p>
                        </section>

                        <section className="space-y-4">
                            <h2 className="text-xl font-semibold text-primary">§ 3 Haftungsausschluss für KI</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Die Lernmaterialien werden durch Künstliche Intelligenz generiert. Wir übernehmen keine Gewähr für die Richtigkeit, Vollständigkeit oder Aktualität der Inhalte. Die Nutzung erfolgt auf eigenes Risiko zur Unterstützung des Lernprozesses.
                            </p>
                        </section>

                        <section className="space-y-4">
                            <h2 className="text-xl font-semibold text-primary">§ 4 Fair Use</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Wir behalten uns das Recht vor, den Zugang zu sperren, wenn eine übermäßige Nutzung festgestellt wird (z.B. durch automatisierte Skripte), die die Stabilität des Systems gefährdet.
                            </p>
                        </section>
                    </div>
                </div>
            </div>
        </div>
    );
}
