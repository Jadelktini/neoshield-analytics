class FraudEngine:
    """Moteur d'arbitrage hybride : Hard Rules + AI Score."""
    
    @staticmethod
    def evaluate(payload, ai_risk_score: float, velocity_kmh: float) -> tuple[str, str, str]:
        # Rule 1 : Hard Rule - KYC non vérifié pour des sommes importantes
        if payload.kyc_status != "VERIFIED" and payload.amount > 500:
            return "REJECTED", "KYC non vérifié pour montant > 500€", "BLOCKED"
        
        # Rule 2 : Hard Rule - Vitesse physique impossible (Impossible Travel)
        if velocity_kmh > 900.0 and payload.amount > 1000:
            return "REJECTED", f"Impossibilité physique de déplacement ({velocity_kmh:.1f} km/h)", "BLOCKED"

        # Rule 3 : Soft Rule - Risque IA Très Élevé
        if ai_risk_score >= 0.75:
            return "REJECTED", f"Score de risque IA élevé ({ai_risk_score:.4f})", "BLOCKED"
        
        # Rule 4 : Soft Rule - Challenge 3D Secure requis
        if 0.35 <= ai_risk_score < 0.75:
            return "CHALLENGE_3DS", f"Risque modéré ({ai_risk_score:.4f}) - Vérification requise", "BIOMETRIC_3DS"

        # Rule 5 : Approbation standard
        return "APPROVED", f"Risque faible ({ai_risk_score:.4f}) - Transaction validée", "NONE"