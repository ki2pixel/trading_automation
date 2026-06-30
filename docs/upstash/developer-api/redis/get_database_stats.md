> ## Documentation Index
> Fetch the complete documentation index at: https://upstash.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Get Database Stats

> This endpoint gets detailed stats of a database.



## OpenAPI

````yaml /devops/developer-api/openapi.yml get /redis/stats/{id}
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
  /redis/stats/{id}:
    get:
      tags:
        - redis
      summary: Get Database Stats
      description: This endpoint gets detailed stats of a database.
      operationId: getDatabaseStats
      parameters:
        - name: id
          in: path
          description: The ID of the database
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Database stats retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DatabaseStats'
      security:
        - basicAuth: []
components:
  schemas:
    DatabaseStats:
      type: object
      properties:
        monitor_count:
          $ref: '#/components/schemas/TimeSeriesData'
          description: Monitor count
        daily_net_commands:
          type: integer
          description: Total number of commands executed today
          example: 7
        daily_read_requests:
          type: integer
          description: Total number of read requests executed today
          example: 7
        daily_write_requests:
          type: integer
          description: Total number of write requests executed today
          example: 0
        connection_count:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Connection count over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
        keyspace:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Total number of keys in the database over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
        throughput:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Throughput on database connections over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
        diskusage:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Disk usage over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
        latencymean:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Average latency over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
        latency_99:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: 99th percentile latency over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
        read_latency_mean:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Average read latency over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
        read_latency_99:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: 99th percentile read latency over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
        write_latency_mean:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Average write latency over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
        write_latency_99:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: 99th percentile write latency over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
        hits:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Cache hits over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
        misses:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Cache misses over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
        read:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Read requests over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
        write:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Write requests over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
        dailyrequests:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Daily requests over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
            - x: 2025-09-04 15:12:52.76649148 +0000 UTC
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
        dailybilling:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Daily billing amounts over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
            - x: 2025-09-04 15:12:52.76649148 +0000 UTC
              'y': 1.333
        dailybandwidth:
          type: integer
          description: Total daily bandwidth usage in bytes
          example: 50444740913
        bandwidths:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Bandwidth usage over time
          example:
            - x: 2025-08-31 15:12:52.799480932 +0000 UTC
              'y': 0
            - x: 2025-09-04 15:12:52.76649148 +0000 UTC
              'y': 7
        total_monthly_bandwidth:
          type: integer
          description: Total bandwidth used in current month (bytes)
          example: 7
        total_monthly_requests:
          type: integer
          description: Total requests in current month
          example: 7
        total_monthly_read_requests:
          type: integer
          description: Total read requests in current month
          example: 7
        total_monthly_write_requests:
          type: integer
          description: Total write requests in current month
          example: 0
        total_monthly_script_requests:
          type: integer
          description: Total script requests in current month
          example: 0
        queue_optimized:
          type: boolean
          description: Whether queue optimization is enabled for the database
          example: false
        total_monthly_storage:
          type: integer
          description: Total storage used in current month (bytes)
          example: 0
        current_storage:
          type: integer
          description: Current storage used (bytes)
          example: 0
        total_monthly_billing:
          type: number
          format: float
          description: Total cost in current month
          example: 222.33902763855485
        command_counts:
          type: array
          description: Command-specific counts over time
          items:
            $ref: '#/components/schemas/CommandCount'
          example:
            - metric_identifier: EXISTS
              data_points:
                - x: 2025-08-31 15:12:52.799480932 +0000 UTC
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
    CommandCount:
      type: object
      properties:
        metric_identifier:
          type: string
          description: Command name or metric identifier
          example: EXISTS
        data_points:
          type: array
          items:
            $ref: '#/components/schemas/TimeSeriesData'
          description: Data points for the given command
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic

````