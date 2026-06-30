> ## Documentation Index
> Fetch the complete documentation index at: https://upstash.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Change Database Plan

> This endpoint changes the plan of a Redis database.



## OpenAPI

````yaml /devops/developer-api/openapi.yml post /redis/{id}/change-plan
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
  /redis/{id}/change-plan:
    post:
      tags:
        - redis
      summary: Change Database Plan
      description: This endpoint changes the plan of a Redis database.
      operationId: changePlan
      parameters:
        - name: id
          in: path
          description: The ID of the database whose plan will be changed
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ChangePlanRequest'
      responses:
        '200':
          description: Plan changed successfully
          content:
            application/json:
              schema:
                type: string
                example: OK
      security:
        - basicAuth: []
components:
  schemas:
    ChangePlanRequest:
      type: object
      properties:
        database_id:
          type: string
          description: ID of the database
          example: 6gcefvfd-9627-2tz5-4l71-c5679g19d2g4
        plan_name:
          type: string
          description: The new plan for the database
          enum:
            - free
            - payg
            - fixed_250mb
            - fixed_1gb
            - fixed_5gb
            - fixed_10gb
            - fixed_50gb
            - fixed_100gb
            - fixed_500gb
          example: fixed_1gb
        auto_upgrade:
          type: boolean
          description: Whether to enable automatic upgrade for the database
          example: true
        prod_pack_enabled:
          type: boolean
          description: Whether to enable the production pack for the database
          example: false
      required:
        - plan_name
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic

````