"""
Agent factory for creating agents from configuration.
"""

from pathlib import Path
from typing import Dict, Optional

import yaml

from src.agents.base_agent import AgentConfig, BaseAgent
from src.agents.expert_agent import ExpertAgent
from src.agents.general_agent import GeneralAgent
from src.llm import OpenRouterClient
from src.rag import HybridRetriever
from src.utils import get_logger

logger = get_logger(__name__)


class AgentFactory:
    """
    Factory for creating and managing agents.
    
    Loads agent configurations from YAML and creates agent instances.
    """
    
    # Agent type mapping
    AGENT_TYPES = {
        "expert_agent": ExpertAgent,
        "general_agent": GeneralAgent,
    }
    
    def __init__(
        self,
        config_path: Path,
        llm_client: OpenRouterClient,
        retriever: Optional[HybridRetriever] = None,
        channel_reader = None,
    ):
        """
        Initialize agent factory.
        
        Args:
            config_path: Path to agents.yaml config file
            llm_client: LLM client for agents
            retriever: RAG retriever for agents
            channel_reader: Channel reader tool (optional, can be set later)
        """
        self.config_path = config_path
        self.llm_client = llm_client
        self.retriever = retriever
        self.channel_reader = channel_reader
        
        # Load configuration
        self.config = self._load_config()
        
        # Create agents
        self.agents: Dict[str, BaseAgent] = {}
        self._create_agents()
        
        # Build channel routing
        self.channel_routing = self._build_channel_routing()
        self.default_agent = self.config.get("routing", {}).get("default_agent", "general_agent")
        
        logger.info(
            "agent_factory_initialized",
            agents=list(self.agents.keys()),
            default_agent=self.default_agent,
            channel_routing=self.channel_routing,
        )
    
    def _load_config(self) -> dict:
        """Load agent configuration from YAML."""
        logger.info("loading_agent_config", path=str(self.config_path))
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        if "agents" not in config:
            raise ValueError("Invalid agent config: 'agents' key not found")
        
        logger.info(
            "agent_config_loaded",
            agents_count=len(config["agents"]),
        )
        
        return config
    
    def _create_agents(self):
        """Create agent instances from configuration."""
        for agent_id, agent_config in self.config["agents"].items():
            logger.info("creating_agent", agent_id=agent_id)
            
            # Create AgentConfig object
            config = AgentConfig(
                name=agent_config["name"],
                description=agent_config["description"],
                channels=agent_config.get("channels", []),
                system_prompt=agent_config["system_prompt"],
                rag_enabled=agent_config.get("rag_enabled", False),
                rag_sources=agent_config.get("rag_sources", []),
                supports_vision=agent_config.get("supports_vision", False),
                include_images=agent_config.get("include_images", False),
                max_history=agent_config.get("max_history", 5),
                tools=agent_config.get("tools", []),
                response=agent_config.get("response", {}),
            )
            
            # Get agent class
            agent_class = self.AGENT_TYPES.get(agent_id)
            if not agent_class:
                logger.warning(
                    "unknown_agent_type",
                    agent_id=agent_id,
                    available_types=list(self.AGENT_TYPES.keys()),
                )
                continue
            
            # Create agent instance
            if agent_id == "general_agent":
                # GeneralAgent needs channel_reader
                agent = agent_class(
                    config=config,
                    llm_client=self.llm_client,
                    retriever=self.retriever if config.rag_enabled else None,
                    channel_reader=self.channel_reader,
                )
            else:
                agent = agent_class(
                    config=config,
                    llm_client=self.llm_client,
                    retriever=self.retriever if config.rag_enabled else None,
                )
            
            self.agents[agent_id] = agent
            
            logger.info(
                "agent_created",
                agent_id=agent_id,
                name=config.name,
                channels=config.channels,
            )
    
    def _build_channel_routing(self) -> Dict[str, str]:
        """Build channel to agent mapping."""
        routing = {}
        
        # Get routing config
        routing_config = self.config.get("routing", {})
        channel_agents = routing_config.get("channel_agents", {})
        
        # Build mapping
        for channel, agent_id in channel_agents.items():
            routing[channel] = agent_id
            logger.debug("channel_route_added", channel=channel, agent=agent_id)
        
        return routing
    
    def get_agent_for_channel(
        self,
        channel_name: str,
        channel_id: Optional[int] = None,
    ) -> BaseAgent:
        """
        Get appropriate agent for a channel.
        
        Args:
            channel_name: Discord channel name
            channel_id: Discord channel ID (optional, more reliable)
            
        Returns:
            Agent instance
        """
        # Try channel ID first (most reliable)
        if channel_id:
            channel_id_str = str(channel_id)
            agent_id = self.channel_routing.get(channel_id_str)
            
            if agent_id and agent_id in self.agents:
                logger.debug(
                    "agent_selected_by_channel_id",
                    channel_name=channel_name,
                    channel_id=channel_id,
                    agent=agent_id,
                )
                return self.agents[agent_id]
        
        # Fall back to channel name
        agent_id = self.channel_routing.get(channel_name)
        
        if agent_id and agent_id in self.agents:
            logger.debug(
                "agent_selected_by_channel_name",
                channel=channel_name,
                agent=agent_id,
            )
            return self.agents[agent_id]
        
        # Use default agent
        default_agent = self.agents.get(self.default_agent)
        if default_agent:
            logger.debug(
                "agent_selected_default",
                channel=channel_name,
                channel_id=channel_id,
                agent=self.default_agent,
            )
            return default_agent
        
        # Fallback to first available agent
        logger.warning(
            "agent_fallback",
            channel=channel_name,
            default_not_found=self.default_agent,
        )
        return next(iter(self.agents.values()))
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get agent by ID.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent instance or None
        """
        return self.agents.get(agent_id)
    
    def list_agents(self) -> Dict[str, BaseAgent]:
        """Get all agents."""
        return self.agents.copy()
    
    def set_channel_reader(self, channel_reader):
        """
        Set or update channel reader for agents.
        
        This is useful when channel_reader is created after AgentFactory initialization.
        
        Args:
            channel_reader: ChannelReader instance
        """
        self.channel_reader = channel_reader
        
        # Update GeneralAgent with channel_reader
        if "general_agent" in self.agents:
            self.agents["general_agent"].channel_reader = channel_reader
            logger.info("channel_reader_set_on_general_agent")
