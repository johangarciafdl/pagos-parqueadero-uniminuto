import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { KioskService } from "@/client"
import { QRDisplay } from "@/components/Kiosk/QRDisplay"
import { Button } from "@/components/ui/button"
import useCustomToast from "@/hooks/useCustomToast"

const MyQR = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data } = useQuery({
    queryKey: ["my-qr"],
    queryFn: async () => (await KioskService.myQr()).data as { qr_token: string },
  })

  const regenerate = useMutation({
    mutationFn: async () => (await KioskService.regenerateQr()).data as {
      qr_token: string
    },
    onSuccess: () => {
      showSuccessToast("Se generó un nuevo QR; el anterior ya no funciona")
      queryClient.invalidateQueries({ queryKey: ["my-qr"] })
    },
    onError: () => showErrorToast("No se pudo generar un nuevo QR"),
  })

  if (!data) return null

  return (
    <div className="flex max-w-md flex-col gap-4">
      <div>
        <h3 className="text-lg font-semibold py-2">Mi QR</h3>
        <p className="text-muted-foreground text-sm">
          Muestra este código para identificarte en el parqueadero o para
          volver a entrar sin escribir tu ID.
        </p>
      </div>
      <div className="w-fit rounded-lg border p-4">
        <QRDisplay value={data.qr_token} />
      </div>
      <Button
        variant="outline"
        className="w-fit"
        onClick={() => regenerate.mutate()}
        disabled={regenerate.isPending}
      >
        Generar un QR nuevo (invalida el actual)
      </Button>
    </div>
  )
}

export default MyQR
