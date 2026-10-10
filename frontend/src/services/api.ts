import axios, { AxiosInstance, AxiosError } from 'axios'
import { API_BASE_URL, STORAGE_KEYS } from '@/utils/constants'

class ApiClient {
  private client: AxiosInstance
  private token: string | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
    this.token = localStorage.getItem(STORAGE_KEYS.TOKEN)
  }

  private setupInterceptors() {
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          this.clearToken()
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
        }
        return Promise.reject(this.normalizeError(error))
      }
    )
  }

  private normalizeError(error: AxiosError) {
    const data = error.response?.data as any
    return {
      detail: data?.detail || error.message || 'An error occurred',
      code: data?.code,
      status: error.response?.status,
      details: data?.details,
    }
  }

  setToken(token: string | null) {
    this.token = token
    if (token) {
      localStorage.setItem(STORAGE_KEYS.TOKEN, token)
    } else {
      localStorage.removeItem(STORAGE_KEYS.TOKEN)
    }
  }

  clearToken() {
    this.setToken(null)
  }

  getToken(): string | null {
    return this.token
  }

  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.client.get<T>(url, { params })
    return response.data
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post<T>(url, data)
    return response.data
  }

  async patch<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.patch<T>(url, data)
    return response.data
  }

  async delete<T>(url: string, config?: any): Promise<T> {
    const response = await this.client.delete<T>(url, config)
    return response.data
  }

  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.put<T>(url, data)
    return response.data
  }
}

export const apiClient = new ApiClient()
export default apiClient