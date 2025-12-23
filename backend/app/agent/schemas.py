"""Pydantic schemas for block-based exam plans"""
from pydantic import BaseModel, Field
from typing import List


class TopicPlan(BaseModel):
    """Single topic within a block"""
    id: str = Field(description="Unique topic ID, e.g., 'topic_01'")
    title: str = Field(description="Topic title, short and clear", max_length=100)
    description: str = Field(description="What will be covered", max_length=500)
    estimated_paragraphs: int = Field(default=3, ge=2, le=10)
    difficulty_level: int = Field(default=3, ge=1, le=5, description="Complexity of this topic (1-5 points)")
    estimated_study_minutes: int = Field(default=15, ge=5, le=60, description="Estimated minutes to study this topic")


class BlockPlan(BaseModel):
    """Block of related topics (chapter/module)"""
    block_id: str = Field(description="Block ID, e.g., 'block_01'")
    block_title: str = Field(description="Block theme/chapter name", max_length=100)
    topics: List[TopicPlan] = Field(description="Related topics in this block")


class ExamPlan(BaseModel):
    """Complete exam plan with blocks"""
    total_topics: int = Field(ge=2)
    total_blocks: int = Field(ge=1)
    blocks: List[BlockPlan] = Field(min_length=1)
    
    def get_all_topics(self) -> List[TopicPlan]:
        """Get flattened list of all topics"""
        return [topic for block in self.blocks for topic in block.topics]
    
    def get_topic_by_id(self, topic_id: str) -> TopicPlan | None:
        """Find topic by ID"""
        for block in self.blocks:
            for topic in block.topics:
                if topic.id == topic_id:
                    return topic
        return None
    
    def get_block_by_topic_id(self, topic_id: str) -> BlockPlan | None:
        """Find which block contains a topic"""
        for block in self.blocks:
            if any(t.id == topic_id for t in block.topics):
                return block
        return None


class ReflectionResult(BaseModel):
    """Result of AI content verification (Reflector Agent)"""
    is_accurate: bool = Field(description="Whether the content is factually accurate according to source")
    pedagogical_alignment: bool = Field(description="Whether the tone and complexity align with target level and scientific principles")
    errors: List[str] = Field(default_factory=list, description="List of factual errors or inaccuracies found")
    hallucinations: List[str] = Field(default_factory=list, description="List of details not found in source material")
    suggestions: str = Field(default="", description="Instructions on how to correct the errors")
