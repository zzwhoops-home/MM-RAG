import logging
from typing import Any, Iterable, List, Literal, Optional, cast

import voyageai  # type: ignore
from langchain_core.embeddings import Embeddings
from langchain_core.utils import secret_from_env
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    SecretStr,
    model_validator,
)
from typing_extensions import Self

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 10

class VoyageAIEmbeddingsMM(BaseModel, Embeddings):
    """
    Taken from Langchain's VoyageAIEmbeddings use case, modified to use VoyageAI's
    multimodal embeddings model. Uses only text input.

    Example:
        .. code-block:: python

            from langchain_voyageai import VoyageAIEmbeddings

            model = VoyageAIEmbeddings()
    """

    _client: voyageai.Client = PrivateAttr()
    _aclient: voyageai.client_async.AsyncClient = PrivateAttr()
    model: str = "voyage-02"
    batch_size: int

    output_dimension: int = 1024 # MODIFIED, ALL MM embeddings are 1024-dimensional
    show_progress_bar: bool = False
    truncation: bool = True
    voyage_api_key: SecretStr = Field(
        alias="api_key",
        default_factory=secret_from_env(
            "VOYAGE_API_KEY",
            error_message="Must set `VOYAGE_API_KEY` environment variable or "
            "pass `api_key` to VoyageAIEmbeddings constructor.",
        ),
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="before")
    @classmethod
    def default_values(cls, values: dict) -> Any:
        """Set default batch size based on model"""
        batch_size = values.get("batch_size")
        if batch_size is None:
            values["batch_size"] = DEFAULT_BATCH_SIZE # using "default" of 10 instead of different sizes for each model
        return values

    @model_validator(mode="after")
    def validate_environment(self) -> Self:
        """Validate that VoyageAI credentials exist in environment."""
        api_key_str = self.voyage_api_key.get_secret_value()
        self._client = voyageai.Client(api_key=api_key_str)
        self._aclient = voyageai.AsyncClient(api_key=api_key_str)
        return self

    def _get_batch_iterator(self, texts: List[str]) -> Iterable:
        if self.show_progress_bar:
            try:
                from tqdm.auto import tqdm  # type: ignore
            except ImportError as e:
                raise ImportError(
                    "Must have tqdm installed if `show_progress_bar` is set to True. "
                    "Please install with `pip install tqdm`."
                ) from e

            _iter = tqdm(range(0, len(texts), self.batch_size))
        else:
            _iter = range(0, len(texts), self.batch_size)  # type: ignore

        return _iter

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""
        embeddings: List[List[float]] = []

        _iter = self._get_batch_iterator(texts)
        for i in _iter:
            formatted_texts = [[text] for text in texts[i : i + self.batch_size]]

            r = self._client.multimodal_embed(
                texts=formatted_texts,
                model=self.model,
                input_type="document",
                truncation=self.truncation,
                output_dimension=self.output_dimension,
            ).embeddings
            embeddings.extend(cast(Iterable[List[float]], r))
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        r = self._client.multimodal_embed(
            [text],
            model=self.model,
            input_type="query",
            truncation=self.truncation,
            output_dimension=self.output_dimension,
        ).embeddings[0]
        return cast(List[float], r)

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings: List[List[float]] = []

        _iter = self._get_batch_iterator(texts)
        for i in _iter:
            formatted_texts = [[text] for text in texts[i : i + self.batch_size]]

            r = await self._aclient.multimodal_embed(
                texts=formatted_texts,
                model=self.model,
                input_type="document",
                truncation=self.truncation,
                output_dimension=self.output_dimension,
            )
            embeddings.extend(cast(Iterable[List[float]], r.embeddings))

        return embeddings

    async def aembed_query(self, text: str) -> List[float]:
        r = await self._aclient.multimodal_embed(
            [text],
            model=self.model,
            input_type="query",
            truncation=self.truncation,
            output_dimension=self.output_dimension,
        )
        return cast(List[float], r.embeddings[0])