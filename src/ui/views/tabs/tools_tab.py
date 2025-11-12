"""
Tools Tab - Manages tool deployment to Elastic Agent Builder.
"""

import streamlit as st
import logging
import os
import json

from src.ui.data_loaders import load_demo_queries
from src.ui.query_results_display import QueryResultsDisplay
from .utils import get_module_prefix

logger = logging.getLogger(__name__)


def render_tools_tab(loader):
    """Render the Tools tab content.

    Args:
        loader: The demo module loader instance
    """
    # Import necessary services
    from src.services.agent_builder_service import AgentBuilderService
    from src.services.query_validation_service import QueryValidationService

    # Initialize services
    validation_service = QueryValidationService(loader.module_path)

    st.markdown("### Tool Management")

    # Initialize Agent Builder service
    try:
        agent_builder = AgentBuilderService()
        connection_valid = agent_builder.validate_connection()

        if not connection_valid['success']:
            st.error(f"❌ Cannot connect to Agent Builder API: {connection_valid.get('error', 'Unknown error')}")
            st.info("Please check your ELASTICSEARCH_KIBANA_URL and ELASTICSEARCH_API_KEY environment variables.")
            st.stop()
    except Exception as e:
        st.error(f"❌ Agent Builder Service not configured: {e}")
        st.info("Please set ELASTICSEARCH_KIBANA_URL and ELASTICSEARCH_API_KEY in your .env file")
        st.stop()

    # Section 1: Deployed Tools
    st.markdown("#### 📤 Deployed Tools")

    # Get list of deployed tools from API
    deployed_response = agent_builder.list_tools()

    if 'error' in deployed_response:
        st.warning(f"Could not fetch deployed tools: {deployed_response['error']}")
        deployed_tools = []
    else:
        # Get tools that belong to this demo
        all_tools = deployed_response.get('tools', [])
        # Extract the company_department prefix for filtering
        module_prefix = get_module_prefix(st.session_state.current_demo_module)
        st.caption(f"Filtering tools with prefix: `{module_prefix}*`")
        deployed_tools = [t for t in all_tools if t.get('id', '').startswith(module_prefix)]

    if deployed_tools:
        for tool in deployed_tools:
            with st.expander(f"🔧 {tool.get('name', tool.get('id', 'Unknown'))}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.json(tool)

                with col2:
                    # Delete button
                    if st.button("🗑️ Delete", key=f"delete_tool_{tool['id']}", use_container_width=True):
                        result = agent_builder.delete_tool(tool['id'])
                        if result.get('success'):
                            st.success(f"Deleted tool: {tool['id']}")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete: {result.get('error')}")
    else:
        st.info("No tools deployed for this demo yet.")

    st.divider()

    # Section 2: Tool Candidates
    st.markdown("#### 🎯 Tool Candidates")
    st.caption("Validated queries from this module ready for deployment as Agent Builder tools")

    # Initialize QueryResultsDisplay for query text extraction
    display = QueryResultsDisplay()

    # Load queries for this specific module
    try:
        queries_dict = load_demo_queries(st.session_state.current_demo_module)
        all_queries = []

        # Combine all query types with their metadata
        for query_type in ['scripted', 'parameterized', 'rag']:
            for i, query in enumerate(queries_dict.get(query_type, []), 1):
                query_id = f"{query_type}_query_{i}"
                # Only check if validated in this module's validation service
                if validation_service.is_query_validated(query_id):
                    all_queries.append({
                        'query_id': query_id,
                        'query': query,
                        'type': query_type,
                        'is_deployed': validation_service.is_tool_deployed(query_id),
                        'metadata': validation_service.get_tool_metadata(query_id) or query.get('tool_metadata')
                    })

        # Separate deployed and undeployed
        undeployed_queries = [q for q in all_queries if not q['is_deployed']]
        already_deployed = [q for q in all_queries if q['is_deployed']]

        if undeployed_queries:
            st.success(f"Found {len(undeployed_queries)} validated queries ready for deployment")

            for candidate in undeployed_queries:
                query_id = candidate['query_id']
                query = candidate['query']
                metadata = candidate['metadata']

                # Create badge for query type
                type_badge = {
                    'scripted': '📊 SCRIPTED',
                    'parameterized': '🔧 PARAMETERIZED',
                    'rag': '🤖 RAG'
                }.get(candidate['type'], '❓ ' + candidate['type'].upper())

                # Use query name or fallback to query_id
                query_name = query.get('name', query_id)

                with st.expander(f"{type_badge} | {query_name}", expanded=False):
                    # Show query type and description
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        # Display query type as a colored badge
                        if candidate['type'] == 'scripted':
                            st.info(f"**Type:** SCRIPTED")
                        elif candidate['type'] == 'parameterized':
                            st.warning(f"**Type:** PARAMETERIZED")
                        elif candidate['type'] == 'rag':
                            st.success(f"**Type:** RAG")
                        else:
                            st.markdown(f"**Type:** {candidate['type'].upper()}")

                    with col2:
                        if query.get('description'):
                            st.markdown(f"**Description:** {query['description']}")

                    # Tool metadata form
                    st.markdown("##### Tool Configuration")

                    # Check if metadata already exists (from saved or pre-generated)
                    # Priority: 1) Saved metadata, 2) Pre-generated from query, 3) Defaults
                    if metadata:
                        tool_id = metadata.get('tool_id', f"{st.session_state.current_demo_module}_{query_id}")
                        tool_description = metadata.get('description', query.get('description', ''))
                        tool_tags = metadata.get('tags', [])
                        sample_question = metadata.get('sample_question', '')
                    elif query.get('tool_metadata'):
                        # Use pre-generated tool metadata from query module
                        pre_gen = query['tool_metadata']
                        tool_id = pre_gen.get('tool_id', f"{st.session_state.current_demo_module}_{query_id}")
                        tool_description = pre_gen.get('description', query.get('description', ''))
                        tool_tags = pre_gen.get('tags', [])
                        sample_question = pre_gen.get('sample_question', '')
                    else:
                        # Fallback defaults
                        tool_id = f"{st.session_state.current_demo_module}_{query_id}"
                        tool_description = query.get('description', '')
                        tool_tags = []
                        sample_question = ''

                    # Input fields for tool metadata (removed name field)
                    new_tool_id = st.text_input(
                        "Tool ID",
                        value=tool_id,
                        key=f"tool_id_{query_id}",
                        help="Unique identifier for the tool in Agent Builder (e.g., company_dept_purpose)"
                    )

                    new_tool_description = st.text_area(
                        "Tool Description",
                        value=tool_description,
                        key=f"tool_desc_{query_id}",
                        height=100,
                        help="First ~50 chars appear in tool list. Start with a brief summary, then explain when to use it."
                    )

                    # Tags input
                    tags_str = st.text_input(
                        "Tags (comma-separated)",
                        value=", ".join(tool_tags) if tool_tags else "",
                        key=f"tool_tags_{query_id}",
                        help="Tags to categorize the tool"
                    )
                    new_tool_tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []

                    # Sample question input
                    new_sample_question = st.text_input(
                        "Sample Agent Question 💬",
                        value=sample_question,
                        key=f"sample_question_{query_id}",
                        help="A realistic user question that would trigger an agent to call this tool",
                        placeholder="e.g., 'Can you show me where we're spending the most on infrastructure?'"
                    )

                    # Info message if using pre-generated metadata
                    if query.get('tool_metadata') and not metadata:
                        st.info("ℹ️ Using pre-generated tool metadata from query module. You can edit these values before saving.")

                    # Parameter Configuration Section (for parameterized/RAG queries)
                    param_optional_settings = {}  # Store which params are optional
                    if candidate['type'] in ['parameterized', 'rag']:
                        st.markdown("##### Parameter Configuration")

                        # Load data profile for parameter extraction
                        from src.ui.data_loaders import load_demo_data_profile
                        data_profile = load_demo_data_profile(st.session_state.current_demo_module)

                        # Extract parameters from query
                        extracted_params = agent_builder.extract_esql_parameters(
                            display._get_query_text(query),
                            data_profile
                        )

                        if extracted_params:
                            st.caption(f"Found {len(extracted_params)} parameter(s) in query")

                            # Create a table-like display for parameters
                            for param_name, param_info in extracted_params.items():
                                with st.container():
                                    col1, col2, col3 = st.columns([2, 2, 1])

                                    with col1:
                                        st.markdown(f"**`{param_name}`**")
                                        st.caption(f"Type: `{param_info['type']}`")

                                    with col2:
                                        st.caption(param_info['description'])

                                    with col3:
                                        # Checkbox to mark as optional
                                        is_optional = st.checkbox(
                                            "Optional",
                                            value=param_info.get('optional', False),
                                            key=f"param_optional_{query_id}_{param_name}",
                                            help="Check to make this parameter optional"
                                        )
                                        param_optional_settings[param_name] = is_optional

                            st.divider()
                        else:
                            st.info("ℹ️ No parameters detected in query")

                    # API Call Preview Section
                    with st.expander("🔍 Preview API Call", expanded=False):
                        st.markdown("##### API Payload Preview")
                        st.caption("This is what will be sent to the Kibana Agent Builder API")

                        # Build the API payload based on current form values
                        api_payload = {
                            "id": new_tool_id,
                            "type": "esql",
                            "description": new_tool_description,
                            "tags": new_tool_tags,
                            "configuration": {
                                "query": display._get_query_text(query)
                            }
                        }

                        # Add parameters using the SAME extraction logic as deployment
                        if candidate['type'] in ['parameterized', 'rag']:
                            # Load data profile for sophisticated parameter detection
                            from src.ui.data_loaders import load_demo_data_profile
                            data_profile = load_demo_data_profile(st.session_state.current_demo_module)

                            # Extract parameters from query (with business date detection)
                            params = agent_builder.extract_esql_parameters(
                                display._get_query_text(query),
                                data_profile
                            )
                            if params:
                                # Apply optional settings from checkboxes
                                for param_name in params:
                                    if param_name in param_optional_settings:
                                        params[param_name]['optional'] = param_optional_settings[param_name]

                                api_payload['configuration']['params'] = params

                        # Display the payload as JSON
                        st.json(api_payload)

                        # Show the API endpoint
                        st.markdown("##### API Endpoint")
                        st.code(f"POST {os.getenv('ELASTICSEARCH_KIBANA_URL', '<KIBANA_URL>')}/api/agent_builder/tools", language="bash")

                        # Show curl command
                        st.markdown("##### Example cURL Command")
                        curl_command = f"""curl -X POST \\
"{os.getenv('ELASTICSEARCH_KIBANA_URL', '<KIBANA_URL>')}/api/agent_builder/tools" \\
-H "Authorization: ApiKey ${{API_KEY}}" \\
-H "Content-Type: application/json" \\
-H "kbn-xsrf: true" \\
-d '{json.dumps(api_payload, indent=2)}'"""
                        st.code(curl_command, language="bash")

                    # Save metadata button
                    col_save, col_deploy = st.columns(2)

                    with col_save:
                        if st.button("💾 Save Metadata", key=f"save_{query_id}", use_container_width=True):
                            # Save the metadata (removed name field)
                            new_metadata = {
                                'tool_id': new_tool_id,
                                'description': new_tool_description,
                                'tags': new_tool_tags,
                                'sample_question': new_sample_question,
                                'query': display._get_query_text(query),
                                'query_type': candidate['type']
                            }

                            # Extract parameters if present
                            if query.get('parameters'):
                                new_metadata['parameters'] = query['parameters']

                            validation_service.save_tool_metadata(query_id, new_metadata)
                            st.success("Metadata saved!")
                            st.rerun()

                    with col_deploy:
                        # Check if ready for deployment
                        is_ready = validation_service.is_tool_ready_for_deployment(query_id)

                        if is_ready:
                            if st.button("🚀 Deploy Tool", key=f"deploy_{query_id}",
                                use_container_width=True, type="primary"):
                                with st.spinner("Deploying tool to Agent Builder..."):
                                    try:
                                        # Get the full metadata
                                        deploy_metadata = validation_service.get_tool_metadata(query_id)

                                        # Create tool configuration
                                        tool_config = {
                                            'id': deploy_metadata['tool_id'],
                                            'type': 'esql',
                                            'description': deploy_metadata['description'],
                                            'tags': deploy_metadata.get('tags', []),
                                            'query': deploy_metadata['query']
                                        }

                                        # Load data profile for sophisticated parameter detection
                                        from src.ui.data_loaders import load_demo_data_profile
                                        data_profile = load_demo_data_profile(st.session_state.current_demo_module)

                                        # Extract parameters from query (with business date detection)
                                        params = agent_builder.extract_esql_parameters(
                                            deploy_metadata['query'],
                                            data_profile
                                        )
                                        if params:
                                            # Apply optional settings from checkboxes
                                            for param_name in params:
                                                if param_name in param_optional_settings:
                                                    params[param_name]['optional'] = param_optional_settings[param_name]

                                            tool_config['params'] = params

                                        # Deploy the tool
                                        result = agent_builder.create_tool(tool_config)

                                        if result.get('success'):
                                            validation_service.mark_tool_deployed(query_id, deploy_metadata['tool_id'])
                                            st.success(f"✅ Tool deployed successfully: {deploy_metadata['tool_id']}")
                                            st.balloons()
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Deployment failed: {result.get('error')}")

                                    except Exception as e:
                                        st.error(f"❌ Error during deployment: {e}")
                        else:
                            st.warning("Please fill in all required fields before deploying")

        # Show already deployed queries at the bottom
        if already_deployed:
            with st.expander(f"✅ Already Deployed ({len(already_deployed)})", expanded=False):
                for deployed in already_deployed:
                    deployed_tool_id = validation_service.get_deployed_tool_id(deployed['query_id'])
                    st.success(f"• {deployed['query'].get('name', deployed['query_id'])} → {deployed_tool_id}")

        if not undeployed_queries and not already_deployed:
            st.info("No validated queries found. Go to the Queries tab and validate queries after testing them.")

    except Exception as e:
        st.error(f"Error loading queries: {e}")
        import traceback
        st.code(traceback.format_exc())
