import { zodResolver } from "@hookform/resolvers/zod"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
} from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { AuthLayout } from "@/components/Common/AuthLayout"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { PasswordInput } from "@/components/ui/password-input"
import useAuth, { isLoggedIn } from "@/hooks/useAuth"

const INSTITUTIONAL_DOMAIN = "@uniminuto.edu.co"

const formSchema = z
  .object({
    email: z
      .email({ message: "Correo inválido" })
      .refine((value) => value.toLowerCase().endsWith(INSTITUTIONAL_DOMAIN), {
        message: `Debes usar tu correo institucional (${INSTITUTIONAL_DOMAIN})`,
      }),
    full_name: z.string().min(1, { message: "El nombre es requerido" }),
    student_id: z.string().min(1, { message: "El ID de estudiante es requerido" }),
    password: z
      .string()
      .min(1, { message: "La contraseña es requerida" })
      .min(8, { message: "La contraseña debe tener al menos 8 caracteres" }),
    confirm_password: z
      .string()
      .min(1, { message: "Confirma tu contraseña" }),
  })
  .refine(
    (data: { password: string; confirm_password: string }) =>
      data.password === data.confirm_password,
    {
      message: "Las contraseñas no coinciden",
      path: ["confirm_password"],
    },
  )

type FormData = z.infer<typeof formSchema>

export const Route = createFileRoute("/signup")({
  component: SignUp,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Crear cuenta - Parqueadero UNIMINUTO",
      },
    ],
  }),
})

function SignUp() {
  const { signUpMutation } = useAuth()
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      email: "",
      full_name: "",
      student_id: "",
      password: "",
      confirm_password: "",
    },
  })

  const onSubmit = (data: FormData) => {
    if (signUpMutation.isPending) return

    // confirm_password no se envía al backend
    const { confirm_password: _confirm_password, ...submitData } = data
    signUpMutation.mutate(submitData)
  }

  return (
    <AuthLayout>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-6"
        >
          <div className="flex flex-col items-center gap-2 text-center">
            <h1 className="text-2xl font-bold">Crear cuenta</h1>
            <p className="text-muted-foreground text-sm">
              Regístrate con tu correo institucional de UNIMINUTO
            </p>
          </div>

          <div className="grid gap-4">
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nombre completo</FormLabel>
                  <FormControl>
                    <Input
                      data-testid="full-name-input"
                      placeholder="Nombre y apellido"
                      type="text"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="student_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>ID / carné de estudiante</FormLabel>
                  <FormControl>
                    <Input
                      data-testid="student-id-input"
                      placeholder="Ej. 0000123456"
                      type="text"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Correo institucional</FormLabel>
                  <FormControl>
                    <Input
                      data-testid="email-input"
                      placeholder={`usuario${INSTITUTIONAL_DOMAIN}`}
                      type="email"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Contraseña</FormLabel>
                  <FormControl>
                    <PasswordInput
                      data-testid="password-input"
                      placeholder="Contraseña"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="confirm_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Confirmar contraseña</FormLabel>
                  <FormControl>
                    <PasswordInput
                      data-testid="confirm-password-input"
                      placeholder="Confirmar contraseña"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <LoadingButton
              type="submit"
              className="w-full"
              loading={signUpMutation.isPending}
            >
              Crear cuenta
            </LoadingButton>
          </div>

          <div className="text-center text-sm">
            ¿Ya tienes cuenta?{" "}
            <RouterLink to="/login" className="underline underline-offset-4">
              Inicia sesión
            </RouterLink>
          </div>
        </form>
      </Form>
    </AuthLayout>
  )
}
