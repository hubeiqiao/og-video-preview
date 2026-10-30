// Mounts the Textures (textures.dev, MIT) on every host with data-texture; the component files are as delivered.
import { createRoot } from "react-dom/client"
import { Settle } from "./settle"
import { Watch } from "./watch"

const T = { settle: Settle, watch: Watch }
document.querySelectorAll<HTMLElement>("[data-texture]").forEach((host) => {
	const C = T[host.dataset.texture as keyof typeof T]
	if (!C) return
	createRoot(host).render(<C tokens={{ "--texture-ink": host.dataset.ink, "--texture-field": host.dataset.field }} />)
})
