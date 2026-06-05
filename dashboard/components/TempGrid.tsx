"use client";

interface TempGridProps {
  cpuTemp: number | null;
  gpuTemp: number | null;
  ssdTemp: number | null;
  mbTemp: number | null;
}

function getTempClass(temp: number | null): string {
  if (temp === null) return "t-ok";
  if (temp >= 80) return "t-hot";
  if (temp >= 68) return "t-warm";
  return "t-ok";
}

function formatTemp(temp: number | null): string {
  if (temp === null) return "—";
  return `${temp}°C`;
}

export default function TempGrid({ cpuTemp, gpuTemp, ssdTemp, mbTemp }: TempGridProps) {
  const items = [
    { label: "CPU Package", value: cpuTemp },
    { label: "GPU Core", value: gpuTemp },
    { label: "Disco SSD", value: ssdTemp },
    { label: "Placa-mãe", value: mbTemp },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Temperaturas</span>
        <span className="badge badge-orange">Monitorando</span>
      </div>
      <div className="temp-grid">
        {items.map((item) => (
          <div key={item.label} className="temp-item">
            <div className={`temp-val ${getTempClass(item.value)}`}>
              {formatTemp(item.value)}
            </div>
            <div className="temp-lbl">{item.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
