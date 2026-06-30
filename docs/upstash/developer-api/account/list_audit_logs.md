> ## Documentation Index
> Fetch the complete documentation index at: https://upstash.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# List Audit Logs

> This endpoint lists all audit logs of user.



## OpenAPI

````yaml /devops/developer-api/openapi.yml get /auditlogs
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
  /auditlogs:
    servers:
      - url: https://api.upstash.com
    get:
      tags:
        - auditlogs
      summary: List Audit Logs
      description: This endpoint lists all audit logs of user.
      operationId: listAuditLogs
      responses:
        '200':
          description: Audit logs retrieved successfully
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/AuditLog'
      security:
        - basicAuth: []
components:
  schemas:
    AuditLog:
      type: object
      properties:
        log_id:
          type: string
          description: Unique identifier for the log entry
          example: ab9744ed-f51c-4z58-a3cj-e3bs756154du
        customer_id:
          type: string
          description: The ID or email of the customer associated with the log
          example: example@example.com
        actor:
          type: string
          description: The user or system that performed the action
          example: example@example.com
        timestamp:
          type: integer
          format: int64
          description: Unix timestamp of when the action occurred
          example: 1764587058
        action:
          type: integer
          description: Numeric ID representing the specific action type
          example: 13
        action_string:
          type: string
          description: Human-readable description of the action
          example: Delete Team
        source:
          type: string
          description: The source method or client used to perform the action
          example: API_KEY - system_tests
        entity:
          type: string
          description: The primary entity affected by the action
          example: test_team
        secondary_entity:
          type: string
          description: A secondary entity affected, "" or "NA" if not applicable
          example: NA
        third_entity:
          type: string
          description: A tertiary entity affected, "" or "NA" if not applicable
          example: ''
        readable_format:
          type: string
          description: formatted string for display purposes
          example: ''
        ip:
          type: string
          format: ipv4
          description: The IP address from which the request originated
          example: 1.2.3.4
        ttl:
          type: integer
          format: int64
          description: Time to live (expiration) timestamp for this log entry
          example: 1780311858
        reason:
          type: string
          description: The reason for the action, if provided
          example: ''
        notes:
          type: string
          description: Additional notes regarding the action
          example: ''
      xml:
        name: audit_log
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic

````