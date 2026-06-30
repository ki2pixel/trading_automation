> ## Documentation Index
> Fetch the complete documentation index at: https://upstash.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Get Search Stats

> Get search statistics for all the search indices associated with the authenticated user



## OpenAPI

````yaml /devops/developer-api/openapi.yml get /search/stats
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
  /search/stats:
    get:
      tags:
        - search
      summary: Get Search Stats
      description: >-
        Get search statistics for all the search indices associated with the
        authenticated user
      operationId: getGlobalSearchStats
      responses:
        '200':
          description: Statistics for the search indices retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GlobalStats'
      security:
        - basicAuth: []
components:
  schemas:
    GlobalStats:
      type: object
      properties:
        record_count:
          type: integer
          description: Total number of indexed records across all indexes
          example: 10
        request:
          type: integer
          description: Total API requests count across all indexes
          example: 10
        bandwidth:
          type: integer
          description: Total bandwidth usage in bytes across all indexes
          example: 750
        storage:
          type: integer
          description: Total storage usage in bytes across all indexes
          example: 950
        billing:
          type: number
          format: float
          description: Current billing amount across all indexes
          example: 0.001
        rerank_count:
          type: integer
          description: Total reranking operations count across all indexes
          example: 0
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic

````