import { useEffect, useRef, useState } from 'react'
import { websocketUrl } from '../services/api'

export function useNetworkStream() {
  const [data, setData] = useState(null)
  const [connected, setConnected] = useState(false)
  const [history, setHistory] = useState([])
  const retry = useRef()

  useEffect(() => {
    let socket
    let disposed = false
    const connect = () => {
      socket = new WebSocket(websocketUrl)
      socket.onopen = () => setConnected(true)
      socket.onmessage = (event) => {
        const next = JSON.parse(event.data)
        setData(next)
        const focus = next.telemetry?.find((row) => row.device_id === 'r1') || next.telemetry?.[0]
        if (focus) {
          setHistory((items) => [...items.slice(-39), {
            time: new Date(focus.timestamp).toLocaleTimeString([], { hour12: false }),
            latency: focus.latency_ms,
            loss: focus.packet_loss_percent,
            bandwidth: focus.bandwidth_utilization,
            cpu: focus.cpu_usage_percent,
            health: next.status.network_health,
          }])
        }
      }
      socket.onclose = () => {
        setConnected(false)
        if (!disposed) retry.current = setTimeout(connect, 1600)
      }
    }
    connect()
    return () => {
      disposed = true
      clearTimeout(retry.current)
      socket?.close()
    }
  }, [])

  return { data, connected, history }
}

