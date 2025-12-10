"""
Vena Analytics Accelerator - Module Configuration
Control which modules are enabled for each deployment
"""

# Module Registry
AVAILABLE_MODULES = {
    'tree_converter': {
        'name': 'Tree Converter',
        'description': 'Convert Excel tree hierarchies to parent-child format',
        'icon': '🌳',
        'version': '1.0',
        'price': 5000,
        'enabled': True  # Set per client
    },
    'hierarchy_validator': {
        'name': 'Hierarchy Validator',
        'description': 'Validate parent-child relationships and Vena restrictions',
        'icon': '✓',
        'version': '1.0',
        'price': 5000,
        'enabled': True  # Set per client
    },
    'data_quality_checker': {
        'name': 'Data Quality Checker',
        'description': 'Customizable CSV/Excel data validation',
        'icon': '🔍',
        'version': '1.0',
        'price': 8000,
        'enabled': False  # Disabled by default
    },
    'allocation_engine': {
        'name': 'Allocation Engine',
        'description': 'Multi-level cost allocation waterfall',
        'icon': '📊',
        'version': '0.5',
        'price': 15000,
        'enabled': False  # Coming soon
    }
}

# Licensing
LICENSE_TYPE = 'basic'  # Options: 'trial', 'basic', 'professional', 'enterprise'

LICENSE_BUNDLES = {
    'trial': {
        'modules': ['tree_converter'],
        'duration_days': 30
    },
    'basic': {
        'modules': ['tree_converter', 'hierarchy_validator'],
        'price': 8000
    },
    'professional': {
        'modules': ['tree_converter', 'hierarchy_validator', 'data_quality_checker'],
        'price': 15000
    },
    'enterprise': {
        'modules': ['tree_converter', 'hierarchy_validator', 'data_quality_checker', 'allocation_engine'],
        'price': 35000
    }
}

def get_enabled_modules():
    """Return list of enabled module keys"""
    if LICENSE_TYPE in LICENSE_BUNDLES:
        # Use bundle configuration
        return LICENSE_BUNDLES[LICENSE_TYPE]['modules']
    else:
        # Use individual module settings
        return [key for key, config in AVAILABLE_MODULES.items() if config['enabled']]

def get_module_tabs():
    """Return list of (name, key) tuples for enabled modules"""
    enabled = get_enabled_modules()
    return [(AVAILABLE_MODULES[key]['name'], key) 
            for key in enabled if key in AVAILABLE_MODULES]
