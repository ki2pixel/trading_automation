> ## Documentation Index
> Fetch the complete documentation index at: https://upstash.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Get Index Stats

> Retrieves statistics and metrics for a specific search index



## OpenAPI

````yaml /devops/developer-api/openapi.yml get /search/{id}/stats
openapi: 3.0.4
info:
  title: Developer API - Upstash
  description: >-
    This is a documentation to specify Developer API endpoints based on the
    OpenAPI 3.0 specification.
  contact:
    name: Support Team
    email: support@upstash.com
  license:
    name: Apache 2.0
    url: https://www.apache.org/licenses/LICENSE-2.0.html
  version: 1.0.0
servers:
  - url: https://api.upstash.com/v2
security: []
tags:
  - name: redis
    description: Manage redis databases.
    externalDocs:
      description: Find out more
      url: https://upstash.com/docs/devops/developer-api/introduction
  - name: teams
    description: Manage teams and team members.
    externalDocs:
      description: Find out more
      url: https://upstash.com/docs/devops/developer-api/introduction
  - name: vector
    description: Manage vector indices.
    externalDocs:
      description: Find out more
      url: https://upstash.com/docs/devops/developer-api/introduction
  - name: search
    description: Manage search indices.
    externalDocs:
      description: Find out more
      url: https://upstash.com/docs/devops/developer-api/introduction
  - name: qstash
    description: Manage QStash.
    externalDocs:
      description: Find out more
      url: https://upstash.com/docs/devops/developer-api/introduction
externalDocs:
  description: Find out more about Upstash
  url: https://upstash.com/
paths:
  /search/{id}/stats:
    get:
      tags:
        - search
      summary: Get Index Stats
      description: Retrieves statistics and metrics for a specific search index
      operationId: getSearchIndexStats
      parameters:
        - name: id
          in: path
          description: The ID of the search index
          required: true
          schema:
            type: string
        - name: period
          in: query
          required: false
          schema:
            type: string
            enum:
              - 1h
              - 3h
              - 12h
              - 1d
              - 3d
              - 7d
              - 30d
            default: 1h
          description: >
            Time period for statistics aggregation. Each period returns 60
            datapoints 

            with intervals adjusted to the period length. 


            Exceptionally for 30 days, it returns 240 datapoints with 3-hour
            intervals for increased granularity.
          example: 3h
      responses:
        '200':
          description: Statistics for the specified search index retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/VectorStats'
      security:
        - basicAuth: []
components:
  schemas:
    VectorStats:
      type: object
      properties:
        pending_index_count:
          type: integer
          description: Number of pending index operations
          example: 1
        current_vector_count:
          type: integer
          description: Current number of vectors in the index
          example: 1000
        daily_query_count:
          type: integer
          description: Total number of query operations executed today
          example: 100
        daily_update_count:
          type: integer
          description: Total number of update operations executed today
          example: 10
        monthly_query_count:
          type: integer
          description: Total query operations in current month
          example: 1000
        monthly_update_count:
          type: integer
          description: Total update operations in current month
          example: 1000
        monthly_bandwidth_usage:
          type: integer
          description: Total bandwidth used in current month (bytes)
          example: 7000
        storage_usage:
          type: integer
          description: Current storage used (bytes)
          example: 7000
        monthly_cost:
          type: number
          format: float
          description: Total cost in current month
          example: 0.5
        daily_update_requests:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Daily update requests over time
          example:
            - x: 2025-10-19 18:33:05.244068975 +0000 UTC
              'y': 1
        daily_query_requests:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Daily query requests over time
          example:
            - x: 2025-10-19 18:33:05.244068975 +0000 UTC
              'y': 7
        daily_bandwidths:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Daily bandwidth usage over time
          example:
            - x: 2025-10-19 18:33:05.244068975 +0000 UTC
              'y': 7
        days:
          type: array
          items:
            type: string
          description: Days of the week for measurement
          example:
            - Sunday
            - Monday
            - Tuesday
            - Wednesday
            - Thursday
        query_throughput:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Query throughput over time
          example:
            - x: 2025-10-23 17:34:00.000 +0000 UTC
              'y': 7
        update_throughput:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Update throughput over time
          example:
            - x: 2025-10-23 17:34:00.000 +0000 UTC
              'y': 7
        query_latency_mean:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Average query latency over time
          example:
            - x: 2025-10-23 17:34:00.000 +0000 UTC
              'y': 0
        query_latency_99:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: 99th percentile query latency over time
          example:
            - x: 2025-10-23 17:34:00.000 +0000 UTC
              'y': 0
        update_latency_mean:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Average update latency over time
          example:
            - x: 2025-10-23 17:34:00.000 +0000 UTC
              'y': 0
        update_latency_99:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: 99th percentile update latency over time
          example:
            - x: 2025-10-23 17:34:00.000 +0000 UTC
              'y': 0
        embeds_latency_mean:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Average embedding latency over time
          example:
            - x: 2025-10-23 17:34:00.000 +0000 UTC
              'y': 0
        embeds_latency_99:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: 99th percentile embedding latency over time
          example:
            - x: 2025-10-23 17:34:00.000 +0000 UTC
              'y': 0
        vector_count:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Vector count over time
          example:
            - x: 2025-10-23 17:35:00.000 +0000 UTC
              'y': 2
        data_size:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Data size over time
          example:
            - x: 2025-10-23 17:35:00.000 +0000 UTC
              'y': 76
        daily_rerank_count:
          type: integer
          description: Total number of rerank operations executed today
          example: 0
        monthly_rerank_count:
          type: integer
          description: Total rerank operations in current month
          example: 10
        daily_rerank_requests:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Daily rerank requests over time
          example:
            - x: 2025-10-19 18:33:05.244068975 +0000 UTC
              'y': 1
        rerank_latency_mean:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Average rerank latency over time
          example:
            - x: 2025-10-23 17:34:00.000 +0000 UTC
              'y': 0
        rerank_latency_99:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: 99th percentile rerank latency over time
          example:
            - x: 2025-10-23 17:34:00.000 +0000 UTC
              'y': 0
    TimeSeriesData:
      type: object
      properties:
        x:
          type: string
          description: Timestamp when measurement was taken
          example: 2023-05-22 10:59:23.426 +0000 UTC
        'y':
          type: number
          description: The measured value
          example: 320
      required:
        - x
        - 'y'
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic

````