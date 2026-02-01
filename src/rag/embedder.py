"""
Embedding generation for text and images.

Supports:
- OpenAI text embeddings
- CLIP image embeddings (optional, requires torch/transformers)
- Batch processing
"""

from __future__ import annotations
from typing import List, Union, Optional, TYPE_CHECKING, Any

import numpy as np
from openai import AsyncOpenAI

from src.utils import get_logger

logger = get_logger(__name__)

# Optional imports for image embeddings (requires torch/transformers)
try:
    import torch
    from PIL import Image
    from transformers import CLIPModel, CLIPProcessor
    TORCH_AVAILABLE = True
except (ImportError, Exception):
    TORCH_AVAILABLE = False
    torch = None  # type: ignore
    Image = None  # type: ignore
    CLIPModel = None  # type: ignore
    CLIPProcessor = None  # type: ignore
    # Image embeddings disabled (torch/transformers not installed)

# Type aliases for when PIL is not available
if TYPE_CHECKING:
    from PIL import Image as PILImage
    ImageType = Union[PILImage.Image, str]
else:
    ImageType = Any


class TextEmbedder:
    """OpenAI text embeddings."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-large",
        dimension: int = 3072,
        batch_size: int = 100,
        base_url: str = None,
    ):
        """
        Initialize text embedder.
        
        Args:
            api_key: OpenAI or OpenRouter API key
            model: Embedding model name
            dimension: Embedding dimension
            batch_size: Batch size for processing
            base_url: Base URL for API (optional, for OpenRouter)
        """
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        
        self.client = AsyncOpenAI(**client_kwargs)
        self.model = model
        self.dimension = dimension
        self.batch_size = batch_size
        
        # Silent init
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for single text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        result = await self.embed_texts([text])
        return result[0]
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with batching.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    dimensions=self.dimension,
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                logger.debug(
                    "text_embeddings_generated",
                    batch_size=len(batch),
                    total_processed=len(all_embeddings),
                )
                
            except Exception as e:
                logger.error(
                    "text_embedding_error",
                    error=str(e),
                    batch_size=len(batch),
                    exc_info=True,
                )
                raise
        
        return all_embeddings
    
    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for search query.
        
        Args:
            query: Query text
        
        Returns:
            Query embedding vector
        """
        return await self.embed_text(query)


class ImageEmbedder:
    """CLIP image embeddings (requires torch/transformers)."""
    
    def __init__(
        self,
        model_name: str = "openai/clip-vit-large-patch14",
        device: str = None,
    ):
        """
        Initialize image embedder with CLIP.
        
        Args:
            model_name: CLIP model name
            device: Device to run model on (cuda/cpu), auto-detected if None
        
        Raises:
            ImportError: If torch/transformers not available
        """
        if not TORCH_AVAILABLE:
            raise ImportError(
                "torch and transformers required for ImageEmbedder. "
                "Install with: pip install torch transformers pillow"
            )
        
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        
        logger.info(
            "image_embedder_initialized",
            model=model_name,
            device=self.device,
        )
    
    def embed_image(self, image: ImageType) -> List[float]:
        """
        Generate CLIP embedding for image.
        
        Args:
            image: PIL Image or path to image
        
        Returns:
            Image embedding vector (normalized)
        """
        # Load image if path provided
        if isinstance(image, str):
            image = Image.open(image).convert("RGB")
        
        # Process image
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate embedding
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
            
            # Normalize embedding
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            # Convert to list
            embedding = image_features.cpu().numpy()[0].tolist()
        
        return embedding
    
    def embed_images(self, images: List[ImageType]) -> List[List[float]]:
        """
        Generate embeddings for multiple images.
        
        Args:
            images: List of PIL Images or image paths
        
        Returns:
            List of image embedding vectors
        """
        embeddings = []
        
        for image in images:
            try:
                embedding = self.embed_image(image)
                embeddings.append(embedding)
                
            except Exception as e:
                logger.error(
                    "image_embedding_error",
                    error=str(e),
                    exc_info=True,
                )
                # Append zero vector on error
                embeddings.append([0.0] * 768)  # CLIP dimension
        
        logger.debug(
            "image_embeddings_generated",
            count=len(embeddings),
        )
        
        return embeddings


class MultimodalEmbedder:
    """Combined text and image embedder."""
    
    def __init__(
        self,
        openai_api_key: str,
        text_model: str = "text-embedding-3-large",
        clip_model: str = "openai/clip-vit-large-patch14",
        text_dimension: int = 3072,
        batch_size: int = 100,
        base_url: str = None,
        enable_image_embeddings: bool = True,
    ):
        """
        Initialize multimodal embedder.
        
        Args:
            openai_api_key: OpenAI or OpenRouter API key
            text_model: Text embedding model
            clip_model: CLIP model name
            text_dimension: Text embedding dimension
            batch_size: Batch size for text embeddings
            base_url: Base URL for API (optional, for OpenRouter)
            enable_image_embeddings: Enable CLIP image embeddings (requires torch)
        """
        self.text_embedder = TextEmbedder(
            api_key=openai_api_key,
            model=text_model,
            dimension=text_dimension,
            batch_size=batch_size,
            base_url=base_url,
        )
        
        # Initialize image embedder only if torch is available and requested
        self.image_embedder: Optional[ImageEmbedder] = None
        if enable_image_embeddings and TORCH_AVAILABLE:
            try:
                self.image_embedder = ImageEmbedder(model_name=clip_model)
                logger.info("multimodal_embedder_initialized", image_support=True)
            except Exception as e:
                logger.warning(
                    "image_embedder_init_failed",
                    error=str(e),
                    fallback="text_only_mode"
                )
        else:
            reason = "disabled" if not enable_image_embeddings else "torch_not_available"
            logger.info("multimodal_embedder_initialized", image_support=False, reason=reason)
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate text embedding."""
        return await self.text_embedder.embed_text(text)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate text embeddings."""
        return await self.text_embedder.embed_texts(texts)
    
    def embed_image(self, image: ImageType) -> List[float]:
        """
        Generate image embedding.
        
        Args:
            image: PIL Image or path to image
        
        Returns:
            Image embedding vector
        
        Raises:
            RuntimeError: If image embeddings not available
        """
        if not self.image_embedder:
            raise RuntimeError(
                "Image embeddings not available. Install torch/transformers or "
                "disable image processing in config."
            )
        return self.image_embedder.embed_image(image)
    
    def embed_images(self, images: List[ImageType]) -> List[List[float]]:
        """
        Generate image embeddings.
        
        Args:
            images: List of PIL Images or image paths
        
        Returns:
            List of image embedding vectors
        
        Raises:
            RuntimeError: If image embeddings not available
        """
        if not self.image_embedder:
            raise RuntimeError(
                "Image embeddings not available. Install torch/transformers or "
                "disable image processing in config."
            )
        return self.image_embedder.embed_images(images)
    
    async def embed_query(self, query: str) -> List[float]:
        """Generate query embedding."""
        return await self.text_embedder.embed_query(query)
