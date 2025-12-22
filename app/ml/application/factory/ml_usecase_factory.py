from app.ml.application.usecase.ml_usecase import MLUseCase
from app.ml.infrastructure.repository.ml_repository_impl import MLRepositoryImpl
from app.ml.infrastructure.vector_db.qdrant_impl import QdrantVectorDBImpl


class MLUseCaseFactory:
    __vector_db_instance = None

    @staticmethod
    def _get_vector_db():
        """Get or create Qdrant vector DB instance (singleton)."""
        if MLUseCaseFactory.__vector_db_instance is None:
            MLUseCaseFactory.__vector_db_instance = QdrantVectorDBImpl()
        return MLUseCaseFactory.__vector_db_instance

    @staticmethod
    def create() -> MLUseCase:
        repository = MLRepositoryImpl.get_instance()
        vector_db = MLUseCaseFactory._get_vector_db()
        return MLUseCase(repository, vector_db)