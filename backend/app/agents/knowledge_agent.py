from app.agents.base import BaseAgent
from app.agents.schemas import KnowledgeAgentInput, KnowledgeAgentOutput, KnowledgeEvidence
from app.services.knowledge_service import get_knowledge_provider
class KnowledgeAgent(BaseAgent[KnowledgeAgentInput, KnowledgeAgentOutput]):
    def __init__(self): super().__init__("Knowledge Agent", "Retrieves grounded reproducibility guidance with source metadata.", KnowledgeAgentInput, KnowledgeAgentOutput)
    def _execute(self, input_data: KnowledgeAgentInput) -> KnowledgeAgentOutput:
        results = get_knowledge_provider().search(input_data.question, top_k=5, mode="hybrid")
        evidence = [KnowledgeEvidence(title=r.title, source=r.source, content=r.content, chunk_id=r.chunk_id, score=r.score) for r in results]
        return KnowledgeAgentOutput(summary=f"Retrieved {len(evidence)} grounded knowledge sources.", evidence=evidence)
