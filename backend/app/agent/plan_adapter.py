"""Adapter to convert between v3.0 ExamPlan and legacy PlanStep format"""
from typing import List
from app.agent.schemas import ExamPlan
from app.agent.state import PlanStep, Priority


def exam_plan_to_steps(plan: ExamPlan) -> List[PlanStep]:
    """
    Convert ExamPlan (v3.0 blocks) to List[PlanStep] (legacy format)
    
    Args:
        plan: ExamPlan with blocks structure
    
    Returns:
        Flat list of PlanStep objects for legacy code
    """
    steps = []
    step_id = 1
    
    for block in plan.blocks:
        for topic in block.topics:
            # Extract numeric ID from topic.id (e.g., "topic_01" -> 1)
            try:
                topic_num = int(topic.id.split('_')[1])
            except (IndexError, ValueError):
                topic_num = step_id
            
            step = PlanStep(
                id=topic_num,
                title=topic.title,
                description=topic.description,
                priority=Priority.MEDIUM,  # Default priority
                estimated_paragraphs=topic.estimated_paragraphs,
                dependencies=[]  # No dependencies in v3.0
            )
            steps.append(step)
            step_id += 1
    
    return steps
