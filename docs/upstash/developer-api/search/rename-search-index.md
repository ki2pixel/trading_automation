> ## Documentation Index
> Fetch the complete documentation index at: https://upstash.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Rename Search Index

> Renames a search index.



## OpenAPI

````yaml /devops/developer-api/openapi.yml post /search/{id}/rename
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
  /search/{id}/rename:
    post:
      tags:
        - search
      summary: Rename Search Index
      description: Renames a search index.
      operationId: renameSearchIndex
      parameters:
        - name: id
          in: path
          description: The ID of the search index
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - name
              properties:
                name:
                  type: string
                  description: New name for the index
                  example: new-index-name
      responses:
        '200':
          description: Search index renamed successfully
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