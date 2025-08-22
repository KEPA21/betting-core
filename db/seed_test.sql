-- db/seed_test.sql
-- Skapa minsta referensdata som testerna förväntar sig

-- Market för 1X2 (godtyckligt UUID, men stabilt)
INSERT INTO core.markets (market_id, code, description)
VALUES ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '1X2', 'Match odds')
ON CONFLICT (market_id) DO NOTHING;

-- Selections (de två som dyker upp i testerna)
INSERT INTO core.selections (selection_id, market_id, code, params)
VALUES 
  ('bea8671c-e889-4e3d-91d3-b407bc186408', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'HOME', NULL),
  ('f92ea776-daf8-44a1-a0c6-3508f092b3a8', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'AWAY', NULL)
ON CONFLICT (selection_id) DO NOTHING;

-- Bookmaker
INSERT INTO core.bookmakers (bookmaker_id, name, country, website)
VALUES ('024c6a47-1a14-4549-935f-31e22e747670', 'TestBook', 'SE', NULL)
ON CONFLICT (bookmaker_id) DO NOTHING;

-- Modell (id + (name,version) som uppfyller uniken)
INSERT INTO core.models (model_id, name, version, metadata)
VALUES ('5c53bd4d-088d-48ca-8530-6d517a6597f9', 'baseline', '1.0', '{}'::jsonb)
ON CONFLICT (model_id) DO NOTHING;
