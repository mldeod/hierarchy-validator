"""
Vena Analytics Accelerator - Workflow Management
Handle data passing between modules
"""

import streamlit as st

def init_workflow_state():
    """Initialize workflow session state variables"""
    if 'workflow_data' not in st.session_state:
        st.session_state.workflow_data = None
    if 'workflow_source' not in st.session_state:
        st.session_state.workflow_source = None
    if 'workflow_target' not in st.session_state:
        st.session_state.workflow_target = None

def send_to_module(data, source_module, target_module):
    """
    Send data from one module to another
    
    Args:
        data: DataFrame or dict to pass
        source_module: Name of source module
        target_module: Name of target module
    """
    st.session_state.workflow_data = data
    st.session_state.workflow_source = source_module
    st.session_state.workflow_target = target_module

def receive_workflow_data(current_module):
    """
    Check if current module should receive workflow data
    
    Args:
        current_module: Name of current module
        
    Returns:
        tuple: (has_data, data, source_module)
    """
    if (st.session_state.workflow_target == current_module and 
        st.session_state.workflow_data is not None):
        
        data = st.session_state.workflow_data
        source = st.session_state.workflow_source
        
        # Clear workflow after receiving
        st.session_state.workflow_data = None
        st.session_state.workflow_source = None
        st.session_state.workflow_target = None
        
        return True, data, source
    
    return False, None, None

def clear_workflow():
    """Clear workflow state"""
    st.session_state.workflow_data = None
    st.session_state.workflow_source = None
    st.session_state.workflow_target = None
