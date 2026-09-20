import { useEffect, useState } from "react"
import QRCode from "qrcode"

interface QRDisplayProps {
  value: string
  size?: number
  className?: string
}

export function QRDisplay({ value, size = 220, className }: QRDisplayProps) {
  const [dataUrl, setDataUrl] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    QRCode.toDataURL(value, { width: size, margin: 1 }).then((url) => {
      if (!cancelled) setDataUrl(url)
    })
    return () => {
      cancelled = true
    }
  }, [value, size])

  if (!dataUrl) {
    return (
      <div
        className={className}
        style={{ width: size, height: size }}
        aria-hidden
      />
    )
  }

  return (
    <img
      src={dataUrl}
      width={size}
      height={size}
      alt="Código QR de tu cuenta"
      className={className}
    />
  )
}
