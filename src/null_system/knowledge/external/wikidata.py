"""External knowledge base connectors for Wikidata and DBpedia."""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID, uuid4

import requests

from ..graph_store import Entity, Relationship
from ..superbit_encoder import SuperBitEncoder

logger = logging.getLogger(__name__)


@dataclass
class ExternalEntity:
    """Represents an entity from external knowledge base."""
    external_id: str
    external_source: str  # wikidata, dbpedia, etc.
    labels: Dict[str, str]  # language -> label mapping
    descriptions: Dict[str, str] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)
    relationships: List[Tuple[str, str, Any]] = field(default_factory=list)  # (predicate, object_type, value)
    aliases: List[str] = field(default_factory=list)
    external_urls: List[str] = field(default_factory=list)


@dataclass
class CacheEntry:
    """Cache entry for external entity data."""
    entity: ExternalEntity
    cached_at: float
    ttl: float = 86400.0  # 24 hours default TTL


class ExternalConnector(ABC):
    """Abstract base for external knowledge base connectors."""
    
    @abstractmethod
    def search_entities(self, query: str, limit: int = 10) -> List[ExternalEntity]:
        pass
    
    @abstractmethod
    def get_entity(self, entity_id: str) -> Optional[ExternalEntity]:
        pass
    
    @abstractmethod
    def get_relationships(self, entity_id: str) -> List[ExternalEntity]:
        pass


class WikidataConnector(ExternalConnector):
    """Wikidata connector for external entity resolution."""
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        rate_limit: float = 1.0  # seconds between requests
    ):
        self.base_url = "https://www.wikidata.org/w/api.php"
        self.cache_dir = cache_dir or Path("./cache/wikidata")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = rate_limit
        self._last_request_time = 0.0
        self._cache: Dict[str, CacheEntry] = {}
        
        # Load cache from disk
        self._load_cache()
        
        logger.info(f"Initialized WikidataConnector with cache at {self.cache_dir}")
    
    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)
        
        self._last_request_time = time.time()
    
    def _load_cache(self) -> None:
        """Load cache from disk."""
        cache_file = self.cache_dir / "cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                for entity_id, entry_data in cache_data.items():
                    entity_data = entry_data["entity"]
                    entity = ExternalEntity(
                        external_id=entity_data["external_id"],
                        external_source=entity_data["external_source"],
                        labels=entity_data["labels"],
                        descriptions=entity_data.get("descriptions", {}),
                        properties=entity_data.get("properties", {}),
                        relationships=entity_data.get("relationships", []),
                        aliases=entity_data.get("aliases", []),
                        external_urls=entity_data.get("external_urls", [])
                    )
                    
                    self._cache[entity_id] = CacheEntry(
                        entity=entity,
                        cached_at=entry_data["cached_at"],
                        ttl=entry_data.get("ttl", 86400.0)
                    )
                
                logger.debug(f"Loaded {len(self._cache)} entries from Wikidata cache")
            except Exception as e:
                logger.warning(f"Failed to load Wikidata cache: {e}")
    
    def _save_cache(self) -> None:
        """Save cache to disk."""
        cache_file = self.cache_dir / "cache.json"
        
        try:
            cache_data = {}
            for entity_id, entry in self._cache.items():
                cache_data[entity_id] = {
                    "entity": {
                        "external_id": entry.entity.external_id,
                        "external_source": entry.entity.external_source,
                        "labels": entry.entity.labels,
                        "descriptions": entry.entity.descriptions,
                        "properties": entry.entity.properties,
                        "relationships": entry.entity.relationships,
                        "aliases": entry.entity.aliases,
                        "external_urls": entry.entity.external_urls
                    },
                    "cached_at": entry.cached_at,
                    "ttl": entry.ttl
                }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.debug(f"Saved {len(self._cache)} entries to Wikidata cache")
        except Exception as e:
            logger.warning(f"Failed to save Wikidata cache: {e}")
    
    def _is_cache_valid(self, entity_id: str) -> bool:
        """Check if cached entry is still valid."""
        if entity_id not in self._cache:
            return False
        
        current_time = time.time()
        entry = self._cache[entity_id]
        
        return (current_time - entry.cached_at) < entry.ttl
    
    def search_entities(self, query: str, limit: int = 10) -> List[ExternalEntity]:
        """Search for entities in Wikidata."""
        logger.debug(f"Searching Wikidata for: {query}")
        
        self._rate_limit()
        
        params = {
            "action": "wbsearchentities",
            "search": query,
            "language": "en",
            "format": "json",
            "limit": limit
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            entities = []
            
            for item in data.get("search", []):
                entity_id = item["id"]
                
                # Check cache first
                if self._is_cache_valid(entity_id):
                    entities.append(self._cache[entity_id].entity)
                    continue
                
                # Fetch full entity data
                full_entity = self._fetch_entity(entity_id)
                if full_entity:
                    entities.append(full_entity)
            
            logger.debug(f"Found {len(entities)} entities in Wikidata")
            return entities
            
        except Exception as e:
            logger.error(f"Failed to search Wikidata: {e}")
            return []
    
    def get_entity(self, entity_id: str) -> Optional[ExternalEntity]:
        """Get entity by ID from Wikidata."""
        # Check cache first
        if self._is_cache_valid(entity_id):
            return self._cache[entity_id].entity
        
        return self._fetch_entity(entity_id)
    
    def _fetch_entity(self, entity_id: str) -> Optional[ExternalEntity]:
        """Fetch entity data from Wikidata API."""
        self._rate_limit()
        
        params = {
            "action": "wbgetentities",
            "ids": entity_id,
            "format": "json",
            "props": "labels|descriptions|aliases|claims|datatype|sitelinks/urls",
            "languages": "en"
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            entities = data.get("entities", {})
            
            if entity_id not in entities:
                return None
            
            entity_data = entities[entity_id]
            
            # Extract labels
            labels = {}
            for lang, label_data in entity_data.get("labels", {}).items():
                labels[lang] = label_data.get("value", "")
            
            # Extract descriptions
            descriptions = {}
            for lang, desc_data in entity_data.get("descriptions", {}).items():
                descriptions[lang] = desc_data.get("value", "")
            
            # Extract aliases
            aliases = []
            for lang, alias_list in entity_data.get("aliases", {}).items():
                for alias_data in alias_list:
                    aliases.append(alias_data.get("value", ""))
            
            # Extract properties from claims
            properties = {}
            for prop_id, prop_data in entity_data.get("claims", {}).items():
                values = []
                for claim in prop_data:
                    mainsnak = claim.get("mainsnak", {})
                    if mainsnak.get("datatype") == "string":
                        values.append(mainsnak.get("datavalue", {}).get("value", ""))
                    elif mainsnak.get("datatype") == "wikibase-entityid":
                        value = mainsnak.get("datavalue", {}).get("value", {})
                        if "id" in value:
                            values.append(value["id"])
                
                if values:
                    properties[prop_id] = values[0] if len(values) == 1 else values
            
            # Extract external URLs
            external_urls = []
            for site_id, url_data in entity_data.get("sitelinks", {}).items():
                if "url" in url_data:
                    external_urls.append(url_data["url"])
            
            # Create external entity
            external_entity = ExternalEntity(
                external_id=entity_id,
                external_source="wikidata",
                labels=labels,
                descriptions=descriptions,
                properties=properties,
                aliases=aliases,
                external_urls=external_urls
            )
            
            # Cache the entity
            self._cache[entity_id] = CacheEntry(
                entity=external_entity,
                cached_at=time.time()
            )
            
            # Periodically save cache
            if len(self._cache) % 10 == 0:
                self._save_cache()
            
            return external_entity
            
        except Exception as e:
            logger.error(f"Failed to fetch entity {entity_id} from Wikidata: {e}")
            return None
    
    def get_relationships(self, entity_id: str) -> List[ExternalEntity]:
        """Get related entities for a given entity."""
        entity = self.get_entity(entity_id)
        if not entity:
            return []
        
        related_entities = []
        
        # Extract related entity IDs from properties
        related_ids = set()
        for prop_name, prop_value in entity.properties.items():
            if isinstance(prop_value, str) and prop_value.startswith("Q"):
                related_ids.add(prop_value)
        
        # Fetch each related entity
        for related_id in related_ids:
            related_entity = self.get_entity(related_id)
            if related_entity:
                related_entities.append(related_entity)
        
        return related_entities


class DBpediaConnector(ExternalConnector):
    """DBpedia connector for external entity resolution."""
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        rate_limit: float = 1.0
    ):
        self.base_url = "https://dbpedia.org/sparql"
        self.cache_dir = cache_dir or Path("./cache/dbpedia")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = rate_limit
        self._last_request_time = 0.0
        self._cache: Dict[str, CacheEntry] = {}
        
        # Load cache from disk
        self._load_cache()
        
        logger.info(f"Initialized DBpediaConnector with cache at {self.cache_dir}")
    
    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)
        
        self._last_request_time = time.time()
    
    def _load_cache(self) -> None:
        """Load cache from disk."""
        cache_file = self.cache_dir / "cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                for entity_id, entry_data in cache_data.items():
                    entity_data = entry_data["entity"]
                    entity = ExternalEntity(
                        external_id=entity_data["external_id"],
                        external_source=entity_data["external_source"],
                        labels=entity_data["labels"],
                        descriptions=entity_data.get("descriptions", {}),
                        properties=entity_data.get("properties", {}),
                        relationships=entity_data.get("relationships", []),
                        aliases=entity_data.get("aliases", []),
                        external_urls=entity_data.get("external_urls", [])
                    )
                    
                    self._cache[entity_id] = CacheEntry(
                        entity=entity,
                        cached_at=entry_data["cached_at"],
                        ttl=entry_data.get("ttl", 86400.0)
                    )
                
                logger.debug(f"Loaded {len(self._cache)} entries from DBpedia cache")
            except Exception as e:
                logger.warning(f"Failed to load DBpedia cache: {e}")
    
    def _save_cache(self) -> None:
        """Save cache to disk."""
        cache_file = self.cache_dir / "cache.json"
        
        try:
            cache_data = {}
            for entity_id, entry in self._cache.items():
                cache_data[entity_id] = {
                    "entity": {
                        "external_id": entry.entity.external_id,
                        "external_source": entry.entity.external_source,
                        "labels": entry.entity.labels,
                        "descriptions": entry.entity.descriptions,
                        "properties": entry.entity.properties,
                        "relationships": entry.entity.relationships,
                        "aliases": entry.entity.aliases,
                        "external_urls": entry.entity.external_urls
                    },
                    "cached_at": entry.cached_at,
                    "ttl": entry.ttl
                }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.debug(f"Saved {len(self._cache)} entries to DBpedia cache")
        except Exception as e:
            logger.warning(f"Failed to save DBpedia cache: {e}")
    
    def _is_cache_valid(self, entity_id: str) -> bool:
        """Check if cached entry is still valid."""
        if entity_id not in self._cache:
            return False
        
        current_time = time.time()
        entry = self._cache[entity_id]
        
        return (current_time - entry.cached_at) < entry.ttl
    
    def search_entities(self, query: str, limit: int = 10) -> List[ExternalEntity]:
        """Search for entities in DBpedia."""
        logger.debug(f"Searching DBpedia for: {query}")
        
        self._rate_limit()
        
        # SPARQL query to search for entities
        sparql_query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dbo: <http://dbpedia.org/ontology/>
        
        SELECT DISTINCT ?resource ?label WHERE {{
            ?resource rdfs:label ?label .
            FILTER(lang(?label) = "en")
            FILTER(contains(lcase(?label), lcase("{query}")))
        }}
        ORDER BY ?label
        LIMIT {limit}
        """
        
        try:
            params = {
                "query": sparql_query,
                "format": "json"
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            entities = []
            
            for binding in data.get("results", {}).get("bindings", []):
                resource_uri = binding.get("resource", {}).get("value", "")
                label = binding.get("label", {}).get("value", "")
                
                if resource_uri and label:
                    # Extract DBpedia resource name
                    resource_name = resource_uri.split("/")[-1]
                    
                    # Check cache first
                    if self._is_cache_valid(resource_name):
                        entities.append(self._cache[resource_name].entity)
                        continue
                    
                    # Fetch full entity data
                    full_entity = self._fetch_entity(resource_name)
                    if full_entity:
                        entities.append(full_entity)
            
            logger.debug(f"Found {len(entities)} entities in DBpedia")
            return entities
            
        except Exception as e:
            logger.error(f"Failed to search DBpedia: {e}")
            return []
    
    def get_entity(self, entity_id: str) -> Optional[ExternalEntity]:
        """Get entity by ID from DBpedia."""
        # Check cache first
        if self._is_cache_valid(entity_id):
            return self._cache[entity_id].entity
        
        return self._fetch_entity(entity_id)
    
    def _fetch_entity(self, entity_id: str) -> Optional[ExternalEntity]:
        """Fetch entity data from DBpedia SPARQL endpoint."""
        self._rate_limit()
        
        # SPARQL query to get entity data
        sparql_query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX dbp: <http://dbpedia.org/property/>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        
        SELECT DISTINCT ?label ?description ?abstract ?wikiPageExternalLink WHERE {{
            <http://dbpedia.org/resource/{entity_id}> rdfs:label ?label .
            FILTER(lang(?label) = "en")
            
            OPTIONAL {{
                <http://dbpedia.org/resource/{entity_id}> dbo:abstract ?abstract .
                FILTER(lang(?abstract) = "en")
            }}
            
            OPTIONAL {{
                <http://dbpedia.org/resource/{entity_id}> foaf:isPrimaryTopicOf ?wikiPageExternalLink .
            }}
        }}
        LIMIT 1
        """
        
        try:
            params = {
                "query": sparql_query,
                "format": "json"
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            bindings = data.get("results", {}).get("bindings", [])
            
            if not bindings:
                return None
            
            binding = bindings[0]
            
            # Extract data
            labels = {"en": binding.get("label", {}).get("value", "")}
            descriptions = {}
            
            if "abstract" in binding:
                descriptions["en"] = binding["abstract"].get("value", "")
            
            external_urls = []
            if "wikiPageExternalLink" in binding:
                external_urls.append(binding["wikiPageExternalLink"].get("value", ""))
            
            # Create external entity
            external_entity = ExternalEntity(
                external_id=entity_id,
                external_source="dbpedia",
                labels=labels,
                descriptions=descriptions,
                properties={},
                aliases=[],
                external_urls=external_urls
            )
            
            # Cache the entity
            self._cache[entity_id] = CacheEntry(
                entity=external_entity,
                cached_at=time.time()
            )
            
            # Periodically save cache
            if len(self._cache) % 10 == 0:
                self._save_cache()
            
            return external_entity
            
        except Exception as e:
            logger.error(f"Failed to fetch entity {entity_id} from DBpedia: {e}")
            return None
    
    def get_relationships(self, entity_id: str) -> List[ExternalEntity]:
        """Get related entities for a given entity."""
        # For simplicity, this is a placeholder
        # A full implementation would query for related entities using SPARQL
        logger.debug(f"DBpedia get_relationships not fully implemented for {entity_id}")
        return []


class ExternalKnowledgeBase:
    """Manager for external knowledge base connectors."""
    
    def __init__(
        self,
        wikidata_connector: Optional[WikidataConnector] = None,
        dbpedia_connector: Optional[DBpediaConnector] = None,
        cache_dir: Optional[Path] = None
    ):
        self.wikidata = wikidata_connector or WikidataConnector(cache_dir)
        self.dbpedia = dbpedia_connector or DBpediaConnector(cache_dir)
        
        logger.info("Initialized ExternalKnowledgeBase with Wikidata and DBpedia connectors")
    
    def search_all_sources(self, query: str, limit: int = 10) -> Dict[str, List[ExternalEntity]]:
        """Search across all external knowledge sources."""
        logger.debug(f"Searching all sources for: {query}")
        
        results = {}
        
        # Search Wikidata
        try:
            results["wikidata"] = self.wikidata.search_entities(query, limit)
        except Exception as e:
            logger.warning(f"Wikidata search failed: {e}")
            results["wikidata"] = []
        
        # Search DBpedia
        try:
            results["dbpedia"] = self.dbpedia.search_entities(query, limit)
        except Exception as e:
            logger.warning(f"DBpedia search failed: {e}")
            results["dbpedia"] = []
        
        return results
    
    def get_entity_from_any_source(self, source: str, entity_id: str) -> Optional[ExternalEntity]:
        """Get entity from a specific source."""
        if source.lower() == "wikidata":
            return self.wikidata.get_entity(entity_id)
        elif source.lower() == "dbpedia":
            return self.dbpedia.get_entity(entity_id)
        else:
            raise ValueError(f"Unknown source: {source}")
    
    def link_external_entities(
        self,
        entities: List[Entity],
        confidence_threshold: float = 0.7
    ) -> List[Tuple[Entity, ExternalEntity, float]]:
        """Link local entities to external knowledge base entities."""
        linked_pairs = []
        
        for entity in entities:
            best_matches = []
            
            # Try to link using entity name/title
            name = (entity.properties.get("name") or 
                   entity.properties.get("title") or 
                   entity.properties.get("label"))
            
            if name:
                # Search all sources
                search_results = self.search_all_sources(str(name), limit=5)
                
                for source, external_entities in search_results.items():
                    for external_entity in external_entities:
                        # Calculate similarity score
                        similarity = self._calculate_similarity(entity, external_entity)
                        
                        if similarity >= confidence_threshold:
                            best_matches.append((external_entity, similarity, source))
            
            # Select best match
            if best_matches:
                best_match = max(best_matches, key=lambda x: x[1])
                linked_pairs.append((entity, best_match[0], best_match[1]))
        
        return linked_pairs
    
    def _calculate_similarity(self, entity: Entity, external_entity: ExternalEntity) -> float:
        """Calculate similarity between local and external entity."""
        similarities = []
        
        # Compare labels/names
        entity_name = (entity.properties.get("name") or 
                      entity.properties.get("title") or 
                      entity.properties.get("label"))
        
        if entity_name and external_entity.labels:
            external_name = external_entity.labels.get("en", "")
            if external_name:
                import difflib
                similarity = difflib.SequenceMatcher(None, str(entity_name).lower(), external_name.lower()).ratio()
                similarities.append(similarity)
        
        # Compare types if available
        if entity.type:
            # Look for type hints in external entity properties
            type_similarity = 0.0
            
            # Simple heuristic: if entity type appears in any property value
            for prop_value in external_entity.properties.values():
                if isinstance(prop_value, str) and entity.type.lower() in prop_value.lower():
                    type_similarity = 0.5
                    break
            
            similarities.append(type_similarity)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def create_test_fixtures(self, fixture_dir: Path, test_entities: List[Tuple[str, str]]) -> None:
        """Create test fixtures with mock external entity data."""
        fixture_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock Wikidata responses
        wikidata_fixture = {}
        dbpedia_fixture = {}
        
        for entity_type, search_term in test_entities:
            try:
                # Mock some results
                wikidata_fixture[search_term] = {
                    "search": [{
                        "id": f"Q{hash(search_term) % 1000000}",
                        "label": f"Mock {entity_type}: {search_term}",
                        "description": f"A mock {entity_type} entity for testing"
                    }]
                }
                
                dbpedia_fixture[search_term] = {
                    "results": {
                        "bindings": [{
                            "resource": {"value": f"http://dbpedia.org/resource/{search_term.replace(' ', '_')}"},
                            "label": {"value": f"Mock {entity_type}: {search_term}"}
                        }]
                    }
                }
            except Exception as e:
                logger.warning(f"Failed to create fixture for {search_term}: {e}")
        
        # Save fixtures
        (fixture_dir / "wikidata_mock.json").write_text(json.dumps(wikidata_fixture, indent=2))
        (fixture_dir / "dbpedia_mock.json").write_text(json.dumps(dbpedia_fixture, indent=2))
        
        logger.info(f"Created test fixtures in {fixture_dir}")