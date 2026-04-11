import JarvisCanvas from '../components/JarvisCanvas'

/**
 * Thin wrapper so the router has a named component to mount. All the real
 * voice UI logic lives in JarvisCanvas.jsx and is owned by the other session.
 */
export default function JarvisPage() {
  return <JarvisCanvas />
}
