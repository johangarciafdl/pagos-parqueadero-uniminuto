import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query"
import { createRouter, RouterProvider } from "@tanstack/react-router"
import { AxiosError } from "axios"
import { StrictMode } from "react"
import ReactDOM from "react-dom/client"
import { client } from "./client/client.gen"
import { ThemeProvider } from "./components/theme-provider"
import { Toaster } from "./components/ui/sonner"
import "./index.css"
import { routeTree } from "./routeTree.gen"

client.setConfig({
  baseURL: import.meta.env.VITE_API_URL ?? "",
  auth: () => localStorage.getItem("access_token") || "",
  // Render (plan gratis) puede tardar decenas de segundos en "despertar" el
  // servicio tras estar inactivo; sin un timeout explícito, un request
  // durante ese arranque se queda colgado indefinidamente en vez de fallar
  // con un mensaje claro que el usuario pueda reintentar.
  timeout: 25000,
})

const handleApiError = (error: Error) => {
  if (
    error instanceof AxiosError &&
    [401, 403].includes(error.response?.status ?? 0)
  ) {
    localStorage.removeItem("access_token")
    window.location.href = "/login"
  }
}

// El token puede quedar apuntando a un usuario que ya no existe (p. ej. tras
// resembrar la base de datos): el backend responde 404 en /users/me en vez
// de 401/403. Solo para ESA consulta puntual tratamos el 404 como sesión
// inválida, para no forzar logout ante cualquier 404 normal de la app
// (un plan no encontrado, un ID de estudiante inexistente, etc).
const handleCurrentUserError = (error: Error, query: { queryKey: unknown }) => {
  const isCurrentUserQuery =
    Array.isArray(query.queryKey) && query.queryKey[0] === "currentUser"
  if (
    isCurrentUserQuery &&
    error instanceof AxiosError &&
    error.response?.status === 404
  ) {
    localStorage.removeItem("access_token")
    window.location.href = "/login"
  }
}

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error, query) => {
      handleApiError(error)
      handleCurrentUserError(error, query)
    },
  }),
  mutationCache: new MutationCache({
    onError: handleApiError,
  }),
})

const router = createRouter({ routeTree })
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
        <Toaster richColors closeButton />
      </QueryClientProvider>
    </ThemeProvider>
  </StrictMode>,
)
