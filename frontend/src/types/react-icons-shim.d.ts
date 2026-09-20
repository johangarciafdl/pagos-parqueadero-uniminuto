// react-icons/fa y fa6 no resolvieron sus declaraciones de tipos en este
// entorno (instalación incompleta por red intermitente). Este shim evita
// bloquear `tsc` para el footer del template (no forma parte de los
// módulos del proyecto); no afecta el comportamiento en tiempo de
// ejecución, solo restaura el tipado mínimo esperado por TypeScript.
declare module "react-icons/fa" {
  import type { ComponentType, SVGAttributes } from "react"
  export type IconType = ComponentType<SVGAttributes<SVGElement>>
  export const FaGithub: IconType
  export const FaLinkedinIn: IconType
}

declare module "react-icons/fa6" {
  import type { ComponentType, SVGAttributes } from "react"
  export type IconType = ComponentType<SVGAttributes<SVGElement>>
  export const FaXTwitter: IconType
}
