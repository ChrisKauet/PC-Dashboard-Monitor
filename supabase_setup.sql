-- Tabela principal de leituras
CREATE TABLE sensor_readings (
  id          BIGSERIAL PRIMARY KEY,
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  cpu_usage   FLOAT,
  cpu_temp    FLOAT,
  cpu_cores   JSONB,        -- array de floats ex: [12.0, 45.0, ...]
  gpu_usage   FLOAT,
  gpu_temp    FLOAT,
  vram_used   FLOAT,        -- MB
  vram_total  FLOAT,        -- MB
  gpu_fan_rpm INT,
  ram_used    FLOAT,        -- GB
  ram_total   FLOAT,        -- GB
  ram_usage   FLOAT,        -- percent
  storage     JSONB,        -- array de objetos de disco
  uptime_sec  INT,
  hostname    TEXT,
  gpu_vendor  TEXT          -- 'amd', 'nvidia', 'intel', ou NULL
);

-- Index para buscar o registro mais recente rapidamente
CREATE INDEX idx_sensor_readings_recorded_at ON sensor_readings (recorded_at DESC);

-- Limpeza automática: manter só as últimas 24h (evitar crescimento infinito)
CREATE OR REPLACE FUNCTION delete_old_sensor_readings()
RETURNS TRIGGER AS $$
BEGIN
  DELETE FROM sensor_readings
  WHERE recorded_at < NOW() - INTERVAL '24 hours';
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_cleanup_sensors
AFTER INSERT ON sensor_readings
EXECUTE FUNCTION delete_old_sensor_readings();