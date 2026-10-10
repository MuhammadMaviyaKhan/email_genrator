import { useEffect, useRef, useState, useCallback } from 'react'
import { WEBSOCKET_URL } from '@/utils/constants'

interface UseWebSocketOptions {
  emailId: string | null
  token?: string | null
  onMessage?: (message: any) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
}

export function useWebSocket({
  emailId,
  token,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<any>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5
  const baseDelay = 1000

  const onMessageRef = useRef(onMessage)
  const onConnectRef = useRef(onConnect)
  const onDisconnectRef = useRef(onDisconnect)
  const onErrorRef = useRef(onError)

  useEffect(() => {
    onMessageRef.current = onMessage
    onConnectRef.current = onConnect
    onDisconnectRef.current = onDisconnect
    onErrorRef.current = onError
  }, [onMessage, onConnect, onDisconnect, onError])

  const connect = useCallback(() => {
    if (!emailId) return

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
      wsRef.current.onclose = null
      wsRef.current.close()
      wsRef.current = null
    }

    const wsUrl = token
      ? `${WEBSOCKET_URL}/ws/${emailId}?token=${token}`
      : `${WEBSOCKET_URL}/ws/${emailId}`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        reconnectAttempts.current = 0
        onConnectRef.current?.()
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          setLastMessage(message)
          onMessageRef.current?.(message)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.onclose = () => {
        setIsConnected(false)
        onDisconnectRef.current?.()

        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1
          const delay = baseDelay * reconnectAttempts.current
          const jitter = delay * 0.25 * (Math.random() * 2 - 1)
          reconnectTimeoutRef.current = setTimeout(connect, delay + jitter)
        }
      }

      ws.onerror = (error) => {
        onErrorRef.current?.(error)
      }
    } catch (err) {
      console.error('WebSocket connection error:', err)
    }
  }, [emailId, token])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    reconnectAttempts.current = 0
    if (wsRef.current) {
      wsRef.current.onclose = null
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
  }, [])

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    isConnected,
    lastMessage,
    sendMessage,
    disconnect,
    reconnect: connect,
  }
}