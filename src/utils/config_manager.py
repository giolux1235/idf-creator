"""
Centralized configuration management.
Eliminates duplicate YAML loading across the codebase.
"""
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class ConfigManager:
    """Singleton-like configuration manager to avoid duplicate file loading."""
    
    _instances: Dict[str, 'ConfigManager'] = {}
    _configs: Dict[str, Dict[str, Any]] = {}
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = str(Path(config_path).resolve())
        
        # Load config if not already loaded
        if self.config_path not in ConfigManager._configs:
            self._load_config()
        
        self._config = ConfigManager._configs[self.config_path]
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                ConfigManager._configs[self.config_path] = yaml.safe_load(f) or {}
        except FileNotFoundError:
            # Create default config if file doesn't exist
            ConfigManager._configs[self.config_path] = {
                'defaults': {
                    'building_type': 'Office',
                    'stories': 3,
                    'floor_area_per_story_m2': 500,
                    'window_to_wall_ratio': 0.4
                },
                'materials': {},
                'hvac': {},
                'simulation': {}
            }
        except Exception as e:
            raise RuntimeError(f"Failed to load config from {self.config_path}: {e}") from e
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary."""
        return self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key (supports dot notation).
        
        Args:
            key: Configuration key (e.g., 'defaults.building_type')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value if value is not None else default
    
    def get_defaults(self) -> Dict[str, Any]:
        """Get default building parameters."""
        return self.config.get('defaults', {})
    
    def get_materials(self) -> Dict[str, Any]:
        """Get material configuration."""
        return self.config.get('materials', {})
    
    def get_hvac(self) -> Dict[str, Any]:
        """Get HVAC configuration."""
        return self.config.get('hvac', {})
    
    def get_simulation(self) -> Dict[str, Any]:
        """Get simulation configuration."""
        return self.config.get('simulation', {})
    
    @classmethod
    def get_instance(cls, config_path: str = "config.yaml") -> 'ConfigManager':
        """
        Get or create a ConfigManager instance for a specific config path.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            ConfigManager instance
        """
        resolved_path = str(Path(config_path).resolve())
        if resolved_path not in cls._instances:
            cls._instances[resolved_path] = cls(resolved_path)
        return cls._instances[resolved_path]
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear configuration cache (useful for testing)."""
        cls._instances.clear()
        cls._configs.clear()

