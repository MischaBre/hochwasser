import { apiRequest } from '@/api/client'
import type { ListStationsParams, StationListResponse } from '@/features/stations/types'

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
