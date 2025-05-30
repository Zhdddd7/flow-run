#!/usr/bin/env bash
set -euo pipefail

# —— 配置区 —— 
PROJECT_ID="we-staging"
REPO_NAME="test-app"
REGION="us"
TAG="latest"
# Dockerfile 前缀，比如 Dockerfile.get / Dockerfile.conv / Dockerfile.flow
DOCKERFILE_PREFIX="$1"
# 镜像名，也用作容器标签
IMAGE_NAME="$1"

# Artifact Registry 地址
REGISTRY_HOST="${REGION}-docker.pkg.dev"
REPOSITORY="${PROJECT_ID}/${REPO_NAME}"
FULL_IMAGE="${REGISTRY_HOST}/${REPOSITORY}/${IMAGE_NAME}:${TAG}"
# FULL_IMAGE="us-docker.pkg.dev/we-staging/test-app/get:latest"


# —— 登录 Artifact Registry —— 
echo "🔑 Authenticating Docker to ${REGISTRY_HOST}"
gcloud auth configure-docker us-docker.pkg.dev

# —— 构建 & 推送 —— 
echo "📦 Building ${FULL_IMAGE} from Dockerfile.${DOCKERFILE_PREFIX}"
docker build \
  --file Dockerfile.${DOCKERFILE_PREFIX} \
  --tag "${FULL_IMAGE}" \
  .

echo "🚀 Pushing ${FULL_IMAGE}"
docker push "${FULL_IMAGE}"

echo "✅ Done: ${FULL_IMAGE}"
