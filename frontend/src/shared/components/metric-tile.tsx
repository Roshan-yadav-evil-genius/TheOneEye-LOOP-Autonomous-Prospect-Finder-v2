import { Card } from './card'

interface MetricTileProps {
  label: string
  value: string
}

export function MetricTile({ label, value }: MetricTileProps) {
  return (
    <Card className="metric-tile">
      <div className="metric-tile__label">{label}</div>
      <div className="metric-tile__value">{value}</div>
    </Card>
  )
}
