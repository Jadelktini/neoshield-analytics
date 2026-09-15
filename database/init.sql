-- =========================================================================
-- NeoShield Analytics - Schéma Initial PostgreSQL
-- =========================================================================

-- Extension pour la génération d'UUIDs si nécessaire
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table des Utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    kyc_status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, VERIFIED, REJECTED
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des Cartes Bancaires
CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    card_brand VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des Transactions
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    card_id INT REFERENCES cards(id) ON DELETE CASCADE,
    amount NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    merchant_category VARCHAR(50),
    merchant_country VARCHAR(2),
    lat NUMERIC(9, 6),
    lon NUMERIC(9, 6),
    ai_risk_score NUMERIC(5, 4),
    status VARCHAR(30), -- APPROVED, REJECTED, CHALLENGE_3DS
    decision_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les recherches de vélocité par carte et par date
CREATE INDEX IF NOT EXISTS idx_transactions_card_date 
ON transactions(card_id, created_at DESC);

-- Données de test (Seed) pour valider l'API immédiatement
INSERT INTO users (id, full_name, kyc_status) VALUES 
(1, 'Alice Dupont', 'VERIFIED'),
(2, 'Bob Martin', 'PENDING')
ON CONFLICT (id) DO NOTHING;

INSERT INTO cards (id, user_id, card_brand) VALUES 
(101, 1, 'Visa'),
(102, 2, 'Mastercard')
ON CONFLICT (id) DO NOTHING;