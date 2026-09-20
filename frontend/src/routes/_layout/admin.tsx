import { useMutation, useQuery, useQueryClient, useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { Suspense } from "react"

import { type PlanPublic, PlansService, type UserPublic, UsersService } from "@/client"
import AddUser from "@/components/Admin/AddUser"
import { columns, type UserTableData } from "@/components/Admin/columns"
import { DataTable } from "@/components/Common/DataTable"
import PendingUsers from "@/components/Pending/PendingUsers"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LoadingButton } from "@/components/ui/loading-button"
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

function UsersTableContent() {
  const { user: currentUser } = useAuth()
  const { data: users } = useSuspenseQuery(getUsersQueryOptions())

  const tableData: UserTableData[] = users.data.map((user: UserPublic) => ({
    ...user,
    isCurrentUser: currentUser?.id === user.id,
  }))

  return <DataTable columns={columns} data={tableData} />
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
              onClick={() => toggleMutation.mutate(plan)}
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
          <h1 className="text-2xl font-bold tracking-tight">Users</h1>
          <p className="text-muted-foreground">
            Manage user accounts and permissions
          </p>
        </div>
        <AddUser />
      </div>
      <PlanControl />
      <UsersTable />
    </div>
  )
}
