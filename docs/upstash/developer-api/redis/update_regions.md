> ## Documentation Index
> Fetch the complete documentation index at: https://upstash.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Update Regions

> Update the regions of a database



## OpenAPI

````yaml /devops/developer-api/openapi.yml post /redis/update-regions/{id}
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
  /redis/update-regions/{id}:
    post:
      tags:
        - redis
      summary: Update Regions
      description: Update the regions of a database
      operationId: updateRegions
      parameters:
        - name: id
          in: path
          description: The ID of your database
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
                read_regions:
                  type: array
                  items:
                    type: string
                    enum:
                      - us-east-1
                      - us-east-2
                      - us-west-1
                      - us-west-2
                      - ca-central-1
                      - eu-central-1
                      - eu-west-1
                      - eu-west-2
                      - sa-east-1
                      - ap-south-1
                      - ap-northeast-1
                      - ap-southeast-1
                      - ap-southeast-2
                  description: Array of Read Regions of the Database
                  example:
                    - us-west-1
                    - us-west-2
              required:
                - read_regions
      responses:
        '200':
          description: Regions updated successfully
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