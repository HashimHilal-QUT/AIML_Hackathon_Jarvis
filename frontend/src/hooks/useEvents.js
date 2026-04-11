import { useCallback, useEffect, useState } from 'react'
import { api } from '../lib/api'

export default function useEvents({ from, to } = {}) {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchEvents = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.getEvents({ from, to })
      setEvents(res?.events || [])
    } catch (e) {
      setError(e?.message || 'Failed to load events')
    } finally {
      setLoading(false)
    }
  }, [from, to])

  useEffect(() => {
    fetchEvents()
  }, [fetchEvents])

  const createEvent = useCallback(
    async (body) => {
      const created = await api.postEvent(body)
      await fetchEvents()
      return created
    },
    [fetchEvents]
  )

  const deleteEvent = useCallback(
    async (id) => {
      await api.deleteEvent(id)
      setEvents((prev) => prev.filter((e) => e.id !== id))
    },
    []
  )

  return { events, loading, error, refetch: fetchEvents, createEvent, deleteEvent }
}
