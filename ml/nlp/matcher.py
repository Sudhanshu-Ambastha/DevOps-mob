from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .embedding_cache import EmbeddingCache
from .errors import AIProviderError
from .features import FEATURE_SCHEMA_VERSION, compute_pair_features, keyword_overlap
from .providers.base import EmbeddingProvider
from .text import TEXT_PREP_VERSION, build_embedding_text, text_hash

MAX_RETURNED_CANDIDATES=3

METHOD_EMBEDDING="embedding"
METHOD_KEYWORD="keyword"


@dataclass
class Submission:
    title:str
    description:str
    tags:list[str]=field(default_factory=list)


@dataclass
class Candidate:
    problem:dict[str, Any]
    rank:int
    score:float
    method:str
    features:dict[str, Any]
    candidate_text_hash:str


@dataclass
class MatchOutcome:
    method:str
    candidates:list[Candidate]
    submission_text_hash:str
    embedding_model:str|None=None
    compared_count:int=0
    ai_error:AIProviderError|None=None
    config:dict[str, Any]=field(default_factory=dict)


class SemanticMatcher:
    def __init__(
        self,
        provider:EmbeddingProvider,
        cache:EmbeddingCache,
        top_k:int,
        min_similarity:float,
        min_keyword_overlap:float,
        pool_size:int,
        max_chars:int
    ):
        self.provider=provider
        self.cache=cache
        self.top_k=min(top_k, MAX_RETURNED_CANDIDATES)
        self.min_similarity=min_similarity
        self.min_keyword_overlap=min_keyword_overlap
        self.pool_size=pool_size
        self.max_chars=max_chars

    async def match(self, submission:Submission, problems:list[dict[str, Any]], use_ai:bool)->MatchOutcome:
        pool=self._select_pool(submission, problems)

        if not use_ai:
            return self._keyword_match(submission, pool)

        # Declined text is never sent to a provider.
        allowed=[problem for problem in pool if problem.get("ai_processing_allowed", False)]

        try:
            return await self._embedding_match(submission, allowed)
        except AIProviderError as error:
            outcome=self._keyword_match(submission, pool)
            outcome.ai_error=error

            return outcome

    def _text_for(self, title:str, description:str)->str:
        return build_embedding_text(title, description, self.max_chars)

    def _select_pool(self, submission:Submission, problems:list[dict[str, Any]])->list[dict[str, Any]]:
        if len(problems) <= self.pool_size:
            return problems

        text=self._text_for(submission.title, submission.description)

        def pool_order(problem:dict[str, Any])->tuple[float, str]:
            overlap=keyword_overlap(text, self._text_for(problem["title"], problem["description"]))

            return (overlap, problem.get("created_at", ""))

        return sorted(problems, key=pool_order, reverse=True)[:self.pool_size]

    async def _embedding_match(self, submission:Submission, pool:list[dict[str, Any]])->MatchOutcome:
        submission_text=self._text_for(submission.title, submission.description)

        if not pool:
            return MatchOutcome(
                method=METHOD_EMBEDDING,
                candidates=[],
                submission_text_hash=text_hash(submission_text),
                embedding_model=self.provider.model_id,
                config=self._config()
            )

        candidate_texts=[self._text_for(problem["title"], problem["description"]) for problem in pool]
        vectors=await self._resolve_vectors([submission_text, *candidate_texts])
        query=np.array(vectors[submission_text], dtype=np.float64)
        scored=[]

        for problem, text in zip(pool, candidate_texts):
            features=self._features(submission, submission_text, problem, text, query, vectors[text])
            score=features["cosine_similarity"]

            if score >= self.min_similarity:
                scored.append((score, features["title_similarity"], problem, features, text))

        scored.sort(key=lambda item:(item[0], item[1]), reverse=True)

        return MatchOutcome(
            method=METHOD_EMBEDDING,
            candidates=self._to_candidates(scored, METHOD_EMBEDDING),
            submission_text_hash=text_hash(submission_text),
            embedding_model=self.provider.model_id,
            compared_count=len(pool),
            config=self._config()
        )

    async def _resolve_vectors(self, texts:list[str])->dict[str, list[float]]:
        vectors:dict[str, list[float]]={}
        missing:list[str]=[]

        for text in dict.fromkeys(texts):
            cached=self.cache.get(text)

            if cached is None:
                missing.append(text)
            else:
                vectors[text]=cached

        if missing:
            fresh=dict(zip(missing, await self.provider.embed(missing)))
            self.cache.put_many(fresh)
            vectors.update(fresh)

        return vectors

    def _features(
        self,
        submission:Submission,
        submission_text:str,
        problem:dict[str, Any],
        problem_text:str,
        query:np.ndarray|None=None,
        vector:list[float]|None=None
    )->dict[str, Any]:
        candidate_vector=None if vector is None else np.array(vector, dtype=np.float64)

        return compute_pair_features(
            submission.title,
            submission_text,
            submission.tags,
            problem["title"],
            problem_text,
            problem.get("tags", []),
            query,
            candidate_vector
        )

    def _keyword_match(self, submission:Submission, pool:list[dict[str, Any]])->MatchOutcome:
        submission_text=self._text_for(submission.title, submission.description)
        scored=[]

        for problem in pool:
            text=self._text_for(problem["title"], problem["description"])
            features=self._features(submission, submission_text, problem, text)
            score=features["keyword_overlap"]

            if score >= self.min_keyword_overlap:
                scored.append((score, features["tag_overlap"], problem, features, text))

        scored.sort(key=lambda item:(item[0], item[1]), reverse=True)

        return MatchOutcome(
            method=METHOD_KEYWORD,
            candidates=self._to_candidates(scored, METHOD_KEYWORD),
            submission_text_hash=text_hash(submission_text),
            compared_count=len(pool),
            config=self._config()
        )

    def _to_candidates(self, scored:list[tuple], method:str)->list[Candidate]:
        candidates=[]

        for index, (score, _, problem, features, text) in enumerate(scored[:self.top_k]):
            candidates.append(Candidate(
                problem=problem,
                rank=index+1,
                score=round(score, 6),
                method=method,
                features=features,
                candidate_text_hash=text_hash(text)
            ))

        return candidates

    def _config(self)->dict[str, Any]:
        return {
            "feature_schema_version":FEATURE_SCHEMA_VERSION,
            "text_prep_version":TEXT_PREP_VERSION,
            "min_similarity":self.min_similarity,
            "min_keyword_overlap":self.min_keyword_overlap,
            "top_k":self.top_k,
            "pool_size":self.pool_size
        }
