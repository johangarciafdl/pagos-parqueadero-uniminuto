import {
  CalendarClock,
  CircleHelp,
  History,
  MessagesSquare,
  ParkingSquare,
  ScanLine,
  UserPlus,
  Users,
} from "lucide-react"

import { SidebarAppearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"
import useAuth from "@/hooks/useAuth"
import { type Item, Main } from "./Main"
import { User } from "./User"

const baseItems: Item[] = [
  { icon: ParkingSquare, title: "Pago / recarga", path: "/" },
  { icon: CalendarClock, title: "Planes mensuales", path: "/plans" },
  { icon: History, title: "Historial", path: "/history" },
  { icon: CircleHelp, title: "FAQ y soporte", path: "/support" },
]

// El personal exento no paga parqueadero: no necesita planes, historial de
// pagos ni soporte de pagos, solo registrar sus vehículos y mostrar el QR.
const exentoItems: Item[] = [
  { icon: ParkingSquare, title: "Mis vehículos y QR", path: "/" },
]

export function AppSidebar() {
  const { user: currentUser } = useAuth()

  // El administrador tampoco paga parqueadero: su propia vista de "Pago /
  // recarga" debe ser la misma simplificada de vehículos y QR que la de
  // personal exento, con los módulos de administración aparte.
  const isExentoLike = currentUser?.role === "EXENTO" || currentUser?.is_superuser

  const items = currentUser?.is_superuser
    ? [
        ...exentoItems,
        { icon: Users, title: "Admin", path: "/admin" },
        { icon: UserPlus, title: "Registrar exento", path: "/staff-register" },
        { icon: ScanLine, title: "Verificar QR", path: "/verify-qr" },
        { icon: MessagesSquare, title: "Soporte (admin)", path: "/support-admin" },
      ]
    : isExentoLike
      ? exentoItems
      : baseItems

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Logo variant="responsive" />
      </SidebarHeader>
      <SidebarContent>
        <Main items={items} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarAppearance />
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
