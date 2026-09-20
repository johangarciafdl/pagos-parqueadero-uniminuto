export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="border-t py-4 px-6">
      <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
        <p className="text-muted-foreground text-sm">
          Parqueadero UNIMINUTO - Pagos UWallet - {currentYear}
        </p>
      </div>
    </footer>
  )
}
