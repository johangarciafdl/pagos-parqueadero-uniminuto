const cop = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
})

export function formatCOP(amount: number): string {
  return cop.format(amount)
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "-"
  return new Date(iso).toLocaleString("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  })
}
