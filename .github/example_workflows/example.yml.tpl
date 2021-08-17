name: 'example1-example2'

env:
  PROJECT_NAME: example-project
  MODULE_NAME: example1-example2
  TF_WORKSPACE: example1-example2

on:
  push:
    branches:
      - master

jobs:
  base:
    name: 'Base Terraform'
    runs-on: self-hosted
    environment: production
    env:
      SUBDIR: base
    container:
      image: ghcr.io/kelseymok/terraform-workspace:latest
      credentials:
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    steps:
    - name: Checkout
      uses: actions/checkout@v2

    - name: Assume Role
      run: assume-role ${PROJECT_NAME}-${MODULE_NAME}-github-runner-aws

    - name: Terraform Setup Workspace
      uses: ./.github/composite-actions/terraform-setup-workspace

    - name: Terraform Init & Apply
      uses: ./.github/composite-actions/terraform-apply

  data-ingestion-test:
    name: 'Test Data Ingestion'
    runs-on: self-hosted
    environment: production
    container:
      image: ghcr.io/kelseymok/pyspark-testing-env:latest
      credentials:
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    steps:
      - name: Checkout
        uses: actions/checkout@v2

      - name: Test Data Ingestion
        env:
          SUBDIR: data-ingestion
        uses: ./.github/composite-actions/pytest

  data-ingestion:
    name: 'Data Ingestion'
    runs-on: self-hosted
    environment: production
    env:
      SUBDIR: data-ingestion
    needs: ["base", "data-ingestion-test"]
    container:
      image: ghcr.io/kelseymok/terraform-workspace:latest
      credentials:
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    steps:
      - name: Checkout
        uses: actions/checkout@v2

      - name: Assume Role
        run: assume-role ${PROJECT_NAME}-${MODULE_NAME}-github-runner-aws

      - name: Upload Main.py
        run: |
          cd ${SUBDIR}/src
          aws s3 cp main.py s3://${PROJECT_NAME}-${MODULE_NAME}/${SUBDIR}/main.py

      - name: Upload Data Ingestion lib
        run: |
          cd ${SUBDIR}
          python setup.py bdist_egg
          filename=$(ls dist)
          aws s3 cp dist/${filename} s3://${PROJECT_NAME}-${MODULE_NAME}/${SUBDIR}/data_ingestion-0.1-py3.egg

      - name: Terraform Setup Workspace
        uses: ./.github/composite-actions/terraform-setup-workspace

      - name: Terraform Init & Apply
        uses: ./.github/composite-actions/terraform-apply

  data-transformation-test:
    name: 'Test Data Transformation'
    runs-on: self-hosted
    environment: production
    container:
      image: ghcr.io/kelseymok/pyspark-testing-env:latest
      credentials:
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    steps:
      - name: Checkout
        uses: actions/checkout@v2

      - name: Test Data Transformation
        env:
          SUBDIR: data-transformation
        uses: ./.github/composite-actions/pytest

  data-transformation:
    name: 'Data Transformation'
    runs-on: self-hosted
    environment: production
    env:
      SUBDIR: data-transformation
    needs: [ "base", "data-transformation-test"]
    container:
      image: ghcr.io/kelseymok/terraform-workspace:latest
      credentials:
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    steps:
      - name: Checkout
        uses: actions/checkout@v2

      - name: Assume Role
        run: assume-role ${PROJECT_NAME}-${MODULE_NAME}-github-runner-aws

      - name: Upload Main.py
        run: |
          cd ${SUBDIR}/src
          aws s3 cp main.py s3://${PROJECT_NAME}-${MODULE_NAME}/${SUBDIR}/main.py

      - name: Upload Data Transformation lib
        run: |
          cd ${SUBDIR}
          python setup.py bdist_egg
          filename=$(ls dist)
          aws s3 cp dist/${filename} s3://${PROJECT_NAME}-${MODULE_NAME}/${SUBDIR}/data_transformation-0.1-py3.egg

      - name: Terraform Setup Workspace
        uses: ./.github/composite-actions/terraform-setup-workspace

      - name: Terraform Init & Apply
        uses: ./.github/composite-actions/terraform-apply

  data-workflow:
    name: 'Data Workflow'
    runs-on: self-hosted
    environment: production
    needs: ["data-ingestion", "data-transformation"]
    env:
      SUBDIR: data-workflow
    container:
      image: ghcr.io/kelseymok/terraform-workspace:latest
      credentials:
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    steps:
      - name: Checkout
        uses: actions/checkout@v2

      - name: Assume Role
        run: assume-role ${PROJECT_NAME}-${MODULE_NAME}-github-runner-aws

      - name: Terraform Setup Workspace
        uses: ./.github/composite-actions/terraform-setup-workspace

      - name: Terraform Init & Apply
        uses: ./.github/composite-actions/terraform-apply

#  destroy:
#    name: 'Destroy all'
#    runs-on: self-hosted
#    environment: production
#    container:
#      image: ghcr.io/kelseymok/terraform-workspace:latest
#      credentials:
#        username: ${{ github.actor }}
#        password: ${{ secrets.GITHUB_TOKEN }}
#
#    steps:
#      - name: Checkout
#        uses: actions/checkout@v2
#
#      - name: Assume Role
#        run: assume-role ${PROJECT_NAME}-${MODULE_NAME}-github-runner-aws
#
#      - name: Terraform Init & Destroy (Data Workflow)
#        env:
#          SUBDIR: data-workflow
#        uses: ./.github/composite-actions/terraform-destroy
#
#      - name: Terraform Init & Destroy (Data Transformation)
#        env:
#          SUBDIR: data-transformation
#        uses: ./.github/composite-actions/terraform-destroy
#
#      - name: Terraform Init & Destroy (Data Ingestion)
#        env:
#          SUBDIR: data-ingestion
#        uses: ./.github/composite-actions/terraform-destroy
#
#      - name: Terraform Init & Destroy (Base)
#        env:
#          SUBDIR: base
#        uses: ./.github/composite-actions/terraform-destroy