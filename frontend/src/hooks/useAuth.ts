import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import {
  type Body_login_login_access_token as AccessToken,
  KioskService,
  type KioskRegister,
  type KioskRegisterResponse,
  type KioskSession,
  LoginService,
  type QRSession,
  type UserPublic,
  UsersService,
} from "@/client"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null
}

const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: async () => (await UsersService.readUserMe()).data,
    enabled: isLoggedIn(),
  })

  // Registro de estudiante: sin contraseña, solo ID + nombre. El backend
  // devuelve de una vez el token de sesión y el qr_token para mostrarlo.
  const kioskRegisterMutation = useMutation({
    mutationFn: async (data: KioskRegister) => {
      const { data: result } = await KioskService.register({ body: data })
      return result as KioskRegisterResponse
    },
    onSuccess: (result) => {
      localStorage.setItem("access_token", result.token.access_token)
      // Limpia todo el caché (no solo "currentUser"): datos de otra sesión
      // en la misma pestaña (otro usuario, o el admin probando) no deben
      // quedar visibles para la cuenta recién creada.
      queryClient.clear()
    },
    onError: handleError.bind(showErrorToast),
  })

  // Reingreso rápido con el ID de estudiante (limitado por intentos).
  const kioskSessionMutation = useMutation({
    mutationFn: async (data: KioskSession) => {
      const { data: token } = await KioskService.sessionByStudentId({ body: data })
      return token
    },
    onSuccess: (token) => {
      if (!token) return
      localStorage.setItem("access_token", token.access_token)
      queryClient.clear()
      navigate({ to: "/" })
    },
    onError: handleError.bind(showErrorToast),
  })

  // Reingreso escaneando el QR personal (token de alta entropía).
  const qrSessionMutation = useMutation({
    mutationFn: async (data: QRSession) => {
      const { data: token } = await KioskService.sessionByQr({ body: data })
      return token
    },
    onSuccess: (token) => {
      if (!token) return
      localStorage.setItem("access_token", token.access_token)
      queryClient.clear()
      navigate({ to: "/" })
    },
    onError: handleError.bind(showErrorToast),
  })

  // Login con correo/contraseña: reservado para el administrador.
  const login = async (data: AccessToken) => {
    const response = await LoginService.loginAccessToken({
      body: data,
    })
    localStorage.setItem("access_token", response.data.access_token)
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      queryClient.clear()
      navigate({ to: "/" })
    },
    onError: handleError.bind(showErrorToast),
  })

  const logout = () => {
    localStorage.removeItem("access_token")
    queryClient.clear()
    navigate({ to: "/login" })
  }

  return {
    kioskRegisterMutation,
    kioskSessionMutation,
    qrSessionMutation,
    loginMutation,
    logout,
    user,
  }
}

export { isLoggedIn }
export default useAuth
