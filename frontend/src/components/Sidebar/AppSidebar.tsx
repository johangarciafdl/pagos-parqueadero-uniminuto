import {
  CalendarClock,
  CircleHelp,
  History,
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

export function AppSidebar() {
  const { user: currentUser } = useAuth()

  const items = currentUser?.is_superuser
    ? [
        ...baseItems,
        { icon: Users, title: "Admin", path: "/admin" },
        { icon: UserPlus, title: "Registrar exento", path: "/staff-register" },
        { icon: ScanLine, title: "Verificar QR", path: "/verify-qr" },
      ]
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
