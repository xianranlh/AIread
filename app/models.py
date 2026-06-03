"""Pydantic 数据模型。"""
from datetime import datetime
from pydantic import BaseModel, Field


class RawItem(BaseModel):
    source: str
    title: str
    url: str
    summary: str | None = None
    metrics: dict = Field(default_factory=dict)
    fetched_at: datetime = Field(default_factory=datetime.now)


class ScoreResult(BaseModel):
    """LLM 打分输出（批量中的一条）。"""
    id: int
    score: float = Field(ge=0, le=10)
    category: str
    tags: list[str] = Field(default_factory=list)
    reason: str = ""
    worth_deep_dive: bool = False


class Explanation(BaseModel):
    """结构化讲解，所有字段中文。"""
    one_liner: str
    problem: str
    how_it_works: str
    highlights: list[str] = Field(default_factory=list)
    getting_started: str = ""
    prerequisites: list[str] = Field(default_factory=list)
    related: list[str] = Field(default_factory=list)
    verdict: str = ""
    confidence_notes: str = ""

    def to_search_text(self) -> str:
        return " ".join([
            self.one_liner, self.problem, self.how_it_works,
            " ".join(self.highlights), self.verdict,
        ])


CATEGORIES = [
    "模型与算法", "推理与部署", "Agent与应用", "开发工具",
    "数据与训练", "多模态", "学术论文", "行业动态", "其他",
]
