import { Link } from "@tanstack/react-router"

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
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-md bg-white p-1",
        extraClassName,
      )}
    >
      <img
        src="/assets/images/uniminuto-logo.svg"
        alt="UNIMINUTO"
        className="h-full w-full object-contain"
      />
    </span>
  )

  const wordmark = (
    <span className="font-semibold tracking-tight whitespace-nowrap">
      Parqueadero
    </span>
  )

  const content =
    variant === "responsive" ? (
      <div className={cn("flex flex-col items-center gap-1.5", className)}>
        {icon("size-14")}
        <span className="group-data-[collapsible=icon]:hidden">
          {wordmark}
        </span>
      </div>
    ) : variant === "icon" ? (
      icon(cn("size-8", className))
    ) : (
      <div className={cn("flex flex-col items-center gap-1.5", className)}>
        {icon("size-16")}
        {wordmark}
      </div>
    )

  if (!asLink) {
    return content
  }

  return <Link to="/">{content}</Link>
}
