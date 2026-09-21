import { useMutation, useQuery, useQueryClient, useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { Suspense, useMemo, useState } from "react"

import { type PlanPublic, PlansService, type UserPublic, UsersService } from "@/client"
import AddUser from "@/components/Admin/AddUser"
import { columns, type UserTableData } from "@/components/Admin/columns"
import { DataTable } from "@/components/Common/DataTable"
import PendingUsers from "@/components/Pending/PendingUsers"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { formatCOP } from "@/lib/format"

function getUsersQueryOptions() {
  return {
    queryFn: async () =>
      (await UsersService.readUsers({ query: { skip: 0, limit: 100 } })).data,
    queryKey: ["users"],
  }
}

export const Route = createFileRoute("/_layout/admin")({
  component: Admin,
  beforeLoad: async () => {
    const { data: user } = await UsersService.readUserMe()
    if (!user.is_superuser) {
      throw redirect({
        to: "/",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Administración - Parqueadero UNIMINUTO",
      },
    ],
  }),
})

type RoleFilter = "all" | "ESTUDIANTE" | "EXENTO" | "INVITADO"
type PlanFilter = "all" | "active" | "inactive"

function UsersTableContent() {
  const { user: currentUser } = useAuth()
  const { data: users } = useSuspenseQuery(getUsersQueryOptions())
  const [search, setSearch] = useState("")
  const [roleFilter, setRoleFilter] = useState<RoleFilter>("all")
  const [planFilter, setPlanFilter] = useState<PlanFilter>("all")

  const tableData: UserTableData[] = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10)
    const term = search.trim().toLowerCase()

    return users.data
      .map((user: UserPublic) => ({
        ...user,
        isCurrentUser: currentUser?.id === user.id,
      }))
      .filter((user) => {
        if (roleFilter !== "all" && user.role !== roleFilter) return false

        if (planFilter !== "all" && user.role !== "EXENTO") {
          const hasActivePlan = !!user.plan_until && user.plan_until >= today
          if (planFilter === "active" && !hasActivePlan) return false
          if (planFilter === "inactive" && hasActivePlan) return false
        }

        if (!term) return true
        return (
          (user.full_name ?? "").toLowerCase().includes(term) ||
          (user.student_id ?? "").toLowerCase().includes(term) ||
          (user.email ?? "").toLowerCase().includes(term)
        )
      })
  }, [users.data, currentUser?.id, search, roleFilter, planFilter])

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          placeholder="Buscar por nombre, ID o correo..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="sm:max-w-xs"
        />
        <Select
          value={roleFilter}
          onValueChange={(value) => setRoleFilter(value as RoleFilter)}
        >
          <SelectTrigger className="sm:w-56">
            <SelectValue placeholder="Rol" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos los roles</SelectItem>
            <SelectItem value="ESTUDIANTE">Estudiante</SelectItem>
            <SelectItem value="INVITADO">Invitado</SelectItem>
            <SelectItem value="EXENTO">Exento / administrativo</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={planFilter}
          onValueChange={(value) => setPlanFilter(value as PlanFilter)}
        >
          <SelectTrigger className="sm:w-56">
            <SelectValue placeholder="Plan mensual" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Plan: todos</SelectItem>
            <SelectItem value="active">Plan activo</SelectItem>
            <SelectItem value="inactive">Plan sin activar</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <DataTable columns={columns} data={tableData} />
    </div>
  )
}

function UsersTable() {
  return (
    <Suspense fallback={<PendingUsers />}>
      <UsersTableContent />
    </Suspense>
  )
}

function PlanControl() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data: plans } = useQuery({
    queryKey: ["admin-plans"],
    queryFn: async () => (await PlansService.listAllPlans()).data?.data ?? [],
  })

  const toggleMutation = useMutation({
    mutationFn: async (plan: PlanPublic) =>
      PlansService.updatePlan({
        path: { plan_id: plan.id },
        body: { active: !plan.active },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-plans"] })
      queryClient.invalidateQueries({ queryKey: ["plans"] })
      showSuccessToast("Plan actualizado")
    },
    onError: (err: Error) => showErrorToast(err.message),
  })

  if (!plans?.length) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle>Plan mensual</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p className="font-medium">{plan.name}</p>
              <p className="text-muted-foreground text-sm">
                {formatCOP(plan.price_cop)} · {plan.duration_days} días ·{" "}
                {plan.active ? "Disponible para comprar" : "Inactivo (oculto)"}
              </p>
            </div>
            <LoadingButton
              variant={plan.active ? "outline" : "default"}
              loading={toggleMutation.isPending}
              onClick={() => {
                if (
                  plan.active &&
                  !window.confirm(
                    "Esto oculta el plan para TODOS los estudiantes y nadie podrá comprarlo hasta que lo actives de nuevo. ¿Seguro que quieres desactivarlo?",
                  )
                ) {
                  return
                }
                toggleMutation.mutate(plan)
              }}
            >
              {plan.active ? "Desactivar" : "Activar"}
            </LoadingButton>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

function Admin() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Usuarios</h1>
          <p className="text-muted-foreground">
            Administra las cuentas, roles y permisos
          </p>
        </div>
        <AddUser />
      </div>
      <PlanControl />
      <UsersTable />
    </div>
  )
}
