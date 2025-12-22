"""Qdrant vector database implementation."""

import logging
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
)

from app.config.settings import settings
from app.ml.application.port.vector_db_port import VectorDBPort

logger = logging.getLogger(__name__)


class QdrantVectorDBImpl(VectorDBPort):
    """Qdrant implementation of VectorDBPort.

    This adapter implements the vector database port using Qdrant for vector storage.
    Supports both local and cloud (AWS) deployments.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        grpc_port: Optional[int] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        """Initialize Qdrant client.

        Args:
            host: Qdrant server host. Defaults to settings.QDRANT_HOST.
            port: Qdrant HTTP port. Defaults to settings.QDRANT_PORT.
            grpc_port: Qdrant gRPC port. Defaults to settings.QDRANT_GRPC_PORT.
            api_key: Qdrant API key for cloud instances. Defaults to settings.QDRANT_API_KEY.
            collection_name: Collection name. Defaults to settings.QDRANT_COLLECTION_NAME.
        """
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self.grpc_port = grpc_port or settings.QDRANT_GRPC_PORT
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME

        # Initialize Qdrant client
        if self.api_key:
            # Cloud Qdrant (AWS or Qdrant Cloud)
            self.client = QdrantClient(
                url=f"https://{self.host}",
                api_key=self.api_key,
            )
        else:
            # Local Qdrant
            self.client = QdrantClient(
                host=self.host,
                port=self.port,
                grpc_port=self.grpc_port,
            )

        # Ensure collection exists
        self.ensure_collection_exists()

    def ensure_collection_exists(self) -> bool:
        """Ensure the collection exists, create if it doesn't."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.QDRANT_VECTOR_SIZE,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Collection {self.collection_name} created successfully")
            else:
                logger.info(f"Collection {self.collection_name} already exists")

            return True
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            return False

    def search_similar(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in the database.
        
        Args:
            query_vector: The query vector to search for.
            limit: Maximum number of results to return.
            score_threshold: Minimum similarity score (0.0 to 1.0).
                           Qdrant uses cosine distance, so we convert:
                           distance_threshold = 1.0 - score_threshold
        """
        try:
            # Qdrant uses cosine distance (0.0 = identical, 2.0 = opposite)
            # For cosine distance: distance = 1 - similarity
            # So if we want similarity >= 0.8, we need distance <= 0.2
            distance_threshold = 1.0 - score_threshold

            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=distance_threshold,  # Qdrant expects distance threshold
            )

            results = []
            for point in search_result:
                # Convert distance to similarity score
                # For cosine distance: similarity = 1 - distance
                similarity_score = 1.0 - point.score
                results.append({
                    "id": point.id,
                    "score": similarity_score,
                    "payload": point.payload or {},
                })

            return results
        except Exception as e:
            logger.error(f"Error searching similar vectors: {e}")
            return []

    def upsert_vectors(
        self,
        vectors: List[Dict[str, Any]]
    ) -> bool:
        """Insert or update vectors in the database."""
        try:
            points = []
            for vec_data in vectors:
                point = PointStruct(
                    id=vec_data["id"],
                    vector=vec_data["vector"],
                    payload=vec_data.get("payload", {}),
                )
                points.append(point)

            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )

            logger.info(f"Successfully upserted {len(points)} vectors")
            return True
        except Exception as e:
            logger.error(f"Error upserting vectors: {e}")
            return False

