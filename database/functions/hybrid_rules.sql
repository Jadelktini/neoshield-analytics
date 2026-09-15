-- =========================================================================
-- Fonctions PL/pgSQL : Règles Métier Hybrides & Calcul de Vélocité
-- =========================================================================

-- Fonction utilitaire : Calcul de la distance orthodromique (Formule de Haversine)
CREATE OR REPLACE FUNCTION calculate_distance_km(
    lat1 NUMERIC, lon1 NUMERIC, lat2 NUMERIC, lon2 NUMERIC
) RETURNS NUMERIC AS $$
DECLARE
    R CONSTANT NUMERIC := 6371.0; -- Rayon moyen de la Terre en km
    dlat NUMERIC;
    dlon NUMERIC;
    a NUMERIC;
    c NUMERIC;
BEGIN
    IF lat1 IS NULL OR lon1 IS NULL OR lat2 IS NULL OR lon2 IS NULL THEN
        RETURN 0.0;
    END IF;
    
    dlat := RADIANS(lat2 - lat1);
    dlon := RADIANS(lon2 - lon1);
    
    a := SIN(dlat / 2.0)^2 + COS(RADIANS(lat1)) * COS(RADIANS(lat2)) * SIN(dlon / 2.0)^2;
    c := 2.0 * ATAN2(SQRT(a), SQRT(1.0 - a));
    
    RETURN R * c;
END;
$$ LANGUAGE plpgsql IMMUTABLE;


-- Fonction principale d'évaluation de la vélocité et des métriques contextuelles
CREATE OR REPLACE FUNCTION evaluate_hybrid_rules(
    p_card_id INT,
    p_amount NUMERIC,
    p_lat NUMERIC,
    p_lon NUMERIC,
    p_merchant_country VARCHAR,
    p_kyc_status VARCHAR
) 
RETURNS TABLE (
    calculated_velocity_kmh DOUBLE PRECISION,
    tx_count_10m INT
) AS $$
DECLARE
    v_last_lat NUMERIC;
    v_last_lon NUMERIC;
    v_last_time TIMESTAMP WITH TIME ZONE;
    v_time_diff_hours DOUBLE PRECISION;
    v_distance_km NUMERIC;
    v_velocity DOUBLE PRECISION := 0.0;
    v_tx_count INT := 0;
BEGIN
    -- 1. Compter les transactions effectuées par cette carte au cours des 10 dernières minutes
    SELECT COUNT(*) INTO v_tx_count
    FROM transactions
    WHERE card_id = p_card_id
      AND created_at >= NOW() - INTERVAL '10 minutes';

    -- 2. Récupérer la dernière transaction enregistrée pour cette carte
    SELECT lat, lon, created_at 
    INTO v_last_lat, v_last_lon, v_last_time
    FROM transactions
    WHERE card_id = p_card_id
    ORDER BY created_at DESC
    LIMIT 1;

    -- 3. Calculer la vitesse physique de déplacement si une transaction précédente existe
    IF v_last_lat IS NOT NULL AND v_last_lon IS NOT NULL AND v_last_time IS NOT NULL THEN
        v_distance_km := calculate_distance_km(v_last_lat, v_last_lon, p_lat, p_lon);
        v_time_diff_hours := EXTRACT(EPOCH FROM (NOW() - v_last_time)) / 3600.0;

        -- Éviter une division par zéro si les requêtes sont simultanées (< 1 seconde)
        IF v_time_diff_hours > 0.000277 THEN
            v_velocity := v_distance_km / v_time_diff_hours;
        ELSE
            v_velocity := 0.0;
        END IF;
    ELSE
        v_velocity := 0.0;
    END IF;

    -- 4. Enregistrer automatiquement la transaction courante dans l'historique
    INSERT INTO transactions (card_id, amount, merchant_country, lat, lon, ai_risk_score, status, decision_reason)
    VALUES (p_card_id, p_amount, p_merchant_country, p_lat, p_lon, 0.00, 'EVALUATING', 'En cours d analyse');

    -- 5. Renvoyer les métriques calculées à l'API FastAPI
    RETURN QUERY SELECT v_velocity, v_tx_count;
END;
$$ LANGUAGE plpgsql;