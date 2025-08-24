BEGIN;

-- Markets & Selections (HOME)
INSERT INTO core.markets (market_id, code, description)
VALUES ('11111111-1111-1111-1111-111111111111', '1X2', 'Match 1X2')
ON CONFLICT (code) DO NOTHING;

INSERT INTO core.selections (selection_id, market_id, code, params)
VALUES ('bea8671c-e889-4e3d-91d3-b407bc186408', '11111111-1111-1111-1111-111111111111', 'HOME', '{}'::jsonb)
ON CONFLICT DO NOTHING;

-- Bookmaker som används i andra tester
INSERT INTO core.bookmakers (bookmaker_id, name, country, website)
VALUES ('024c6a47-1a14-4549-935f-31e22e747670', 'TestBook', 'SE', 'https://example.com')
ON CONFLICT (bookmaker_id) DO NOTHING;

-- Model som predictions refererar till
INSERT INTO core.models (model_id, name, version, metadata)
VALUES ('5c53bd4d-088d-48ca-8530-6d517a6597f9', 'cursor-model', 'cursor-1', '{}'::jsonb)
ON CONFLICT (model_id) DO NOTHING;

-- Två predictions för SAMMA match_id = 'm_cursor_preds_1'
-- (olika version => inte i konflikt med UNIQUE (match_id, model_id, version, selection_id))
INSERT INTO core.predictions
    (prediction_id, match_id, model_id, version, selection_id, probability, odds_fair, features, predicted_at)
VALUES
    ('4cae1ed8-c1ca-4d2f-ab19-25129c4f0ba2', 'm_cursor_preds_1', '5c53bd4d-088d-48ca-8530-6d517a6597f9', 'cursor-1',
     'bea8671c-e889-4e3d-91d3-b407bc186408', 0.580000, 1.8000, '{"i":3}'::jsonb, '2025-02-02 10:59:00+00'),
    ('7f7d2f6a-1b2c-4c3d-8e9f-000000000002', 'm_cursor_preds_1', '5c53bd4d-088d-48ca-8530-6d517a6597f9', 'cursor-2',
     'bea8671c-e889-4e3d-91d3-b407bc186408', 0.590000, 1.8200, '{"i":4}'::jsonb, '2025-02-02 11:00:15+00')
    ('7f7d2f6a-1b2c-4c3d-8e9f-000000000003', 'm_cursor_preds_1','5c53bd4d-088d-48ca-8530-6d517a6597f9','cursor-3',
     'bea8671c-e889-4e3d-91d3-b407bc186408', 0.610000, 1.8500, '{"i":5}'::jsonb, '2025-02-02 11:02:30+00'),
    ('7f7d2f6a-1b2c-4c3d-8e9f-000000000004','m_cursor_preds_1', '5c53bd4d-088d-48ca-8530-6d517a6597f9', 'cursor-4',
     'bea8671c-e889-4e3d-91d3-b407bc186408', 0.620000, 1.8700, '{"i":6}'::jsonb, '2025-02-02 11:04:45+00')
ON CONFLICT DO NOTHING;

COMMIT;