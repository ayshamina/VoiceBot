/**
 * useHealth.js — Custom hook that polls the backend health endpoint.
 * Returns { data, loading, error } and auto-refreshes every 15 seconds.
 */
import { useState, useEffect, useCallback } from 'react'
import { getHealth } from '../services/api'

export function useHealth(pollIntervalMs = 15_000) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  const fetch = useCallback(async () => {
    try {
      const res = await getHealth()
      setData(res)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetch()
    const id = setInterval(fetch, pollIntervalMs)
    return () => clearInterval(id)
  }, [fetch, pollIntervalMs])

  return { data, loading, error, refresh: fetch }
}
