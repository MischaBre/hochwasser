import { apiRequest } from '@/api/client'
import type {
  ListStationsParams,
  StationListResponse,
  StationMeasurement,
} from '@/features/stations/types'

const toQuery = (params: ListStationsParams): string => {
  const query = new URLSearchParams()

  if (params.search?.trim()) {
    query.set('search', params.search.trim())
  }

  if (typeof params.limit === 'number') {
    query.set('limit', String(params.limit))
  }

  if (typeof params.offset === 'number') {
    query.set('offset', String(params.offset))
  }

  const uuids = (params.uuids ?? []).map((candidate) => candidate.trim()).filter(Boolean)
  if (uuids.length > 0) {
    query.set('uuids', uuids.join(','))
  }

  const queryString = query.toString()
  return queryString.length > 0 ? `?${queryString}` : ''
}

export const listStations = (params: ListStationsParams = {}): Promise<StationListResponse> => {
  return apiRequest<StationListResponse>(`/v1/stations${toQuery(params)}`)
}

export const listStationMeasurements = (
  stationUuid: string,
  start: string = 'P3D',
): Promise<StationMeasurement[]> => {
  const query = new URLSearchParams()
  if (start.trim()) {
    query.set('start', start.trim())
  }
  const queryString = query.toString()
  const suffix = queryString ? `?${queryString}` : ''
  return apiRequest<StationMeasurement[]>(`/v1/stations/${encodeURIComponent(stationUuid)}/measurements${suffix}`)
}

export const listStationForecast = (stationUuid: string): Promise<StationMeasurement[]> => {
  return apiRequest<StationMeasurement[]>(`/v1/stations/${encodeURIComponent(stationUuid)}/forecast`)
}

export const listPublicStations = (params: ListStationsParams = {}): Promise<StationListResponse> => {
  return apiRequest<StationListResponse>(`/v1/public/stations${toQuery(params)}`)
}

export const listPublicStationMeasurements = (
  stationUuid: string,
  start: string = 'P3D',
): Promise<StationMeasurement[]> => {
  const query = new URLSearchParams()
  if (start.trim()) {
    query.set('start', start.trim())
  }
  const queryString = query.toString()
  const suffix = queryString ? `?${queryString}` : ''
  return apiRequest<StationMeasurement[]>(`/v1/public/stations/${encodeURIComponent(stationUuid)}/measurements${suffix}`)
}

export const listPublicStationForecast = (stationUuid: string): Promise<StationMeasurement[]> => {
  return apiRequest<StationMeasurement[]>(`/v1/public/stations/${encodeURIComponent(stationUuid)}/forecast`)
}
