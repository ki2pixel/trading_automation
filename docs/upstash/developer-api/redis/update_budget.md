> ## Documentation Index
> Fetch the complete documentation index at: https://upstash.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Update Database Budget

> This endpoint updates the monthly budget of a Redis database.



## OpenAPI

````yaml /devops/developer-api/openapi.yml patch /redis/update-budget/{id}
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
  /redis/update-budget/{id}:
    patch:
      tags:
        - redis
      summary: Update Database Budget
      description: This endpoint updates the monthly budget of a Redis database.
      operationId: updateBudget
      parameters:
        - name: id
          in: path
          description: The ID of the database whose budget will be updated
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                budget:
                  type: integer
                  description: The new monthly budget for the database
              required:
                - budget
      responses:
        '200':
          description: Budget updated successfully
          content:
            application/json:
              schema:
                type: string
                example: OK
      security:
        - basicAuth: []
components:
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic

````