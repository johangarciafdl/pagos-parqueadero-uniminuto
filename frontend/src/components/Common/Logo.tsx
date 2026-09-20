import { Link } from "@tanstack/react-router"
import { ParkingSquare } from "lucide-react"

import { cn } from "@/lib/utils"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

export function Logo({
  variant = "full",
  className,
  asLink = true,
}: LogoProps) {
  const icon = (extraClassName: string) => (
    <ParkingSquare className={cn("shrink-0 text-primary", extraClassName)} />
  )

  const wordmark = (
    <span className="font-semibold tracking-tight whitespace-nowrap">
      Parqueadero UNIMINUTO
    </span>
  )

  const content =
    variant === "responsive" ? (
      <div className={cn("flex items-center gap-2", className)}>
        {icon("size-5")}
        <span className="group-data-[collapsible=icon]:hidden">
          {wordmark}
        </span>
      </div>
    ) : variant === "icon" ? (
      icon(cn("size-5", className))
    ) : (
      <div className={cn("flex items-center gap-2", className)}>
        {icon("size-6")}
        {wordmark}
      </div>
    )

  if (!asLink) {
    return content
  }

  return <Link to="/">{content}</Link>
}
