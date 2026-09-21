import type { ColumnDef } from "@tanstack/react-table"

import type { UserPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { UserActionsMenu } from "./UserActionsMenu"

export type UserTableData = UserPublic & {
  isCurrentUser: boolean
}

export const columns: ColumnDef<UserTableData>[] = [
  {
    accessorKey: "full_name",
    header: "Nombre",
    cell: ({ row }) => {
      const fullName = row.original.full_name
      return (
        <div className="flex items-center gap-2">
          <span
            className={cn("font-medium", !fullName && "text-muted-foreground")}
          >
            {fullName || "N/A"}
          </span>
          {row.original.isCurrentUser && (
            <Badge variant="outline" className="text-xs">
              Tú
            </Badge>
          )}
        </div>
      )
    },
  },
  {
    accessorKey: "student_id",
    header: "ID estudiante",
    cell: ({ row }) => (
      <span className="text-muted-foreground">
        {row.original.student_id ?? "—"}
      </span>
    ),
  },
  {
    accessorKey: "email",
    header: "Correo",
    cell: ({ row }) => (
      <span className="text-muted-foreground">{row.original.email ?? "—"}</span>
    ),
  },
  {
    accessorKey: "role",
    header: "Rol",
    cell: ({ row }) => {
      const { is_superuser, role } = row.original
      const label = is_superuser
        ? "Administrador"
        : role === "EXENTO"
          ? "Exento de pago"
          : role === "INVITADO"
            ? "Invitado"
            : "Estudiante"
      return (
        <Badge variant={is_superuser ? "default" : "secondary"}>{label}</Badge>
      )
    },
  },
  {
    accessorKey: "plan_until",
    header: "Plan mensual",
    cell: ({ row }) => {
      const { role, plan_until } = row.original
      if (role === "EXENTO") {
        return <span className="text-muted-foreground">No aplica</span>
      }
      const isActive = !!plan_until && plan_until >= new Date().toISOString().slice(0, 10)
      return (
        <Badge variant={isActive ? "default" : "outline"}>
          {isActive ? `Activo hasta ${plan_until}` : "Sin activar"}
        </Badge>
      )
    },
  },
  {
    accessorKey: "is_active",
    header: "Estado",
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "size-2 rounded-full",
            row.original.is_active ? "bg-green-500" : "bg-gray-400",
          )}
        />
        <span className={row.original.is_active ? "" : "text-muted-foreground"}>
          {row.original.is_active ? "Activo" : "Inactivo"}
        </span>
      </div>
    ),
  },
  {
    id: "actions",
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => (
      <div className="flex justify-end">
        <UserActionsMenu user={row.original} />
      </div>
    ),
  },
]
