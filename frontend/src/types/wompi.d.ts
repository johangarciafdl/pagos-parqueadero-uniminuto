export interface WompiWidgetResult {
  transaction: {
    id: string
    status: "APPROVED" | "DECLINED" | "VOIDED" | "ERROR" | "PENDING"
    reference: string
  }
}

export interface WompiWidgetCheckoutOptions {
  currency: "COP"
  amountInCents: number
  reference: string
  publicKey: string
  signature: { integrity: string }
  redirectUrl?: string
}

declare global {
  class WidgetCheckout {
    constructor(options: WompiWidgetCheckoutOptions)
    open(callback: (result: WompiWidgetResult) => void): void
  }
}
