#!/bin/bash
cd "$(dirname "$0")"  # Ensure the script is running in the correct directory

# 1️⃣ Read environment variable
ENV=$1
if [[ -z "$ENV" ]]; then
  echo "❌ You need to specify an environment (staging or production)"
  exit 1
fi

PROJECT_ID=$2
REPO_NAME="test-app"
IMAGE_NAME="prefect-test-app"
CLUSTER_NAME="prefect-test"
REGION="us-central1"
NAMESPACE="default"
DEPLOYMENT_NAME="prefect-test-app"
TAG="latest"

IMAGE="us-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME:$TAG"

echo "🚀 Starting deployment of Backend in $ENV environment to GKE cluster: $CLUSTER_NAME"

# 2️⃣ Authenticate with Google Cloud
gcloud auth configure-docker us-docker.pkg.dev

# 3️⃣ Build & Push Docker image
echo "🐳 Building Docker image: $IMAGE"
docker buildx build --platform linux/amd64 -f Dockerfile.backend -t $IMAGE .
docker push $IMAGE

# 4️⃣ Switch to the correct GKE cluster
if [[ "$CURRENT_PROJECT_ID" != "$PROJECT_ID" ]]; then
  echo "🔄 Switching to the correct project ID: $PROJECT_ID"
  gcloud config set project $PROJECT_ID
  echo "✅ Project ID set to $PROJECT_ID"
fi

# 5️⃣ Get credentials for the GKE cluster
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION

# 6️⃣ Verify the current kubectl context
echo "🔍 Verifying current kubectl context..."
CURRENT_CONTEXT=$(kubectl config current-context)
echo "Current kubectl context: $CURRENT_CONTEXT"


echo "Current cluster: $CURRENT_CLUSTER"
echo "Current namespace: ${CURRENT_NAMESPACE:-default}"

# Get the IP address of the cluster
CLUSTER_IP=$(gcloud container clusters describe $CLUSTER_NAME --region $REGION --format="get(endpoint)")
echo "Cluster IP address: $CLUSTER_IP"

# 7️⃣ Get Deployment and Service names dynamically
DEPLOYMENT_NAME=$(kubectl get deployment -n $NAMESPACE -l app=video-agent-backend-deloyment-1 -o jsonpath="{.items[0].metadata.name}" 2>/dev/null || echo "")
SERVICE_NAME=$(kubectl get svc -n $NAMESPACE -l app=video-agent-backend-deloyment-1 -o jsonpath="{.items[0].metadata.name}" 2>/dev/null || echo "")

echo "🔍 Found Deployment: ${DEPLOYMENT_NAME:-None}"
echo "🔍 Found Service: ${SERVICE_NAME:-None}"

# 8️⃣ Delete old deployment & service if they exist
if [[ -n "$DEPLOYMENT_NAME" ]]; then
  echo "🗑️ Deleting Deployment: $DEPLOYMENT_NAME"
  kubectl delete deployment $DEPLOYMENT_NAME -n $NAMESPACE --ignore-not-found
else
  echo "⚠️ No existing deployment found, skipping deletion."
fi

if [[ -n "$SERVICE_NAME" ]]; then
  echo "🗑️ Patching & Deleting Service: $SERVICE_NAME"
  kubectl patch svc $SERVICE_NAME -n $NAMESPACE --type='merge' -p '{"metadata":{"finalizers":[]}}' || echo "⚠️ Failed to patch finalizers, skipping."
  sleep 5  # Keep the service around for a few seconds to ensure it's deleted
  kubectl delete svc $SERVICE_NAME -n $NAMESPACE --grace-period=0 --force
else
  echo "⚠️ No existing service found, skipping deletion."
fi

# 9️⃣ Apply Kubernetes configurations (dynamically choose the right YAML file)
echo "📜 Applying Kubernetes configuration for $ENV..."

kubectl apply -f "backend/k8s/backend-deployment-$ENV.yaml"  # Dynamic YAML selection
kubectl apply -f "backend/k8s/service-$ENV.yaml"

# 1️⃣0️⃣ Update the backend deployment with the latest image
kubectl set image deployment/$DEPLOYMENT_NAME backend=$IMAGE -n $NAMESPACE


# 1️⃣1️⃣ Restart backend deployment to apply new database authorization
echo "🔄 Restarting backend deployment to apply new database authorization..."
kubectl rollout restart deployment/$DEPLOYMENT_NAME -n $NAMESPACE

# 🔍 **Check the backend deployment status**
kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE

# 🌍 **Retrieve the backend service external IP (only if service exists)**
if [[ -n "$SERVICE_NAME" ]]; then
  kubectl get svc $SERVICE_NAME -n $NAMESPACE
else
  echo "⚠️ No service found, skipping External IP retrieval."
fi

echo "✅ Deployment completed successfully! 🎉"
