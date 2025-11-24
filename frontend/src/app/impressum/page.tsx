import ParticleBackground from "@/components/ParticleBackground";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Impressum() {
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
                        Impressum
                    </h1>

                    <div className="space-y-8 text-foreground">
                        <section className="space-y-4">
                            <h2 className="text-xl font-semibold text-primary">Verantwortlich für den Inhalt</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Ilia Zharikov<br />
                                Österreich<br />
                                Hall in Tirol<br />
                                Salvatorgasse 2a/18
                            </p>
                        </section>

                        <section className="space-y-4">
                            <h2 className="text-xl font-semibold text-primary">Kontakt</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                E-Mail: iljarikov@gmail.com<br />
                                Web: <Link href="https://examai.pro" className="text-primary hover:underline">examai.pro</Link>
                            </p>
                        </section>

                        <section className="space-y-4">
                            <h2 className="text-xl font-semibold text-primary">Unternehmensangaben</h2>
                            <div className="space-y-2 text-muted-foreground leading-relaxed">
                                <p>
                                    <strong className="text-foreground">Unternehmensgegenstand:</strong><br />
                                    Entwicklung und Betrieb von Software für Bildungszwecke (SaaS).
                                </p>
                                <p>
                                    <strong className="text-foreground">Rechtsform:</strong><br />
                                    Privatperson (bzw. in Gründung).
                                </p>
                            </div>
                        </section>
                    </div>
                </div>
            </div>
        </div>
    );
}
