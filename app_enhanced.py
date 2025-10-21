"""
Elastic Agent Builder Demo Generator - Enhanced Version
With validation, task tracking, and state persistence
"""

import streamlit as st
import os
import json
import yaml
from datetime import datetime
from typing import Dict, List, Optional
import logging
from pathlib import Path
import sys
import time
import pandas as pd

# Add project modules to path
sys.path.insert(0, str(Path(__file__).parent))

# Import services
from src.services.validation_service import ValidationService, ValidationTask
from src.services.github_state_manager import GitHubStateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Elastic Demo Builder",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .task-pending { color: #gray; }
    .task-running { color: #3b82f6; animation: pulse 2s infinite; }
    .task-success { color: #10b981; }
    .task-failed { color: #ef4444; }
    .task-warning { color: #f59e0b; }

    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }

    .progress-bar {
        background: linear-gradient(90deg, #3b82f6 0%, #10b981 100%);
        height: 4px;
        border-radius: 2px;
        transition: width 0.3s ease;
    }

    .task-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid;
    }

    .task-card.pending { border-color: #6b7280; }
    .task-card.running { border-color: #3b82f6; }
    .task-card.success { border-color: #10b981; }
    .task-card.failed { border-color: #ef4444; }
    .task-card.warning { border-color: #f59e0b; }
</style>
""", unsafe_allow_html=True)

class DemoBuilderApp:
    def __init__(self):
        self.initialize_session_state()
        self.github_manager = None
        if st.session_state.get('github_token'):
            self.github_manager = GitHubStateManager(
                token=st.session_state.github_token,
                repo="elastic/demo-builder"
            )

    def initialize_session_state(self):
        """Initialize session state variables"""
        if "demo_id" not in st.session_state:
            st.session_state.demo_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if "tasks" not in st.session_state:
            st.session_state.tasks = self.get_initial_tasks()
        if "current_phase" not in st.session_state:
            st.session_state.current_phase = "planning"
        if "validation_results" not in st.session_state:
            st.session_state.validation_results = {}
        if "demo_config" not in st.session_state:
            st.session_state.demo_config = {}
        if "messages" not in st.session_state:
            st.session_state.messages = []

    def get_initial_tasks(self) -> List[Dict]:
        """Get initial task list for demo creation"""
        return [
            {"id": "1", "name": "Customer Research", "phase": "planning", "status": "pending",
             "description": "Research customer and identify use cases"},
            {"id": "2", "name": "Scenario Design", "phase": "planning", "status": "pending",
             "description": "Design custom demo scenario"},
            {"id": "3", "name": "Data Generation", "phase": "generation", "status": "pending",
             "description": "Generate sample datasets"},
            {"id": "4", "name": "Index Creation", "phase": "deployment", "status": "pending",
             "description": "Create Elasticsearch indices"},
            {"id": "5", "name": "Data Upload", "phase": "deployment", "status": "pending",
             "description": "Upload data to Elasticsearch"},
            {"id": "6", "name": "Query Generation", "phase": "generation", "status": "pending",
             "description": "Generate ES|QL queries"},
            {"id": "7", "name": "Query Validation", "phase": "validation", "status": "pending",
             "description": "Validate queries against data"},
            {"id": "8", "name": "Agent Configuration", "phase": "deployment", "status": "pending",
             "description": "Configure Agent Builder"},
            {"id": "9", "name": "Documentation", "phase": "finalization", "status": "pending",
             "description": "Generate demo guide and slides"},
            {"id": "10", "name": "Final Validation", "phase": "finalization", "status": "pending",
             "description": "End-to-end demo validation"}
        ]

    def render_header(self):
        """Render application header"""
        col1, col2, col3 = st.columns([3, 2, 1])

        with col1:
            st.title("🚀 Elastic Demo Builder")
            st.caption(f"Demo ID: {st.session_state.demo_id}")

        with col2:
            if st.session_state.demo_config.get('customer'):
                st.metric("Customer", st.session_state.demo_config['customer'])

        with col3:
            overall_progress = self.calculate_overall_progress()
            st.metric("Progress", f"{overall_progress}%")

    def calculate_overall_progress(self) -> int:
        """Calculate overall progress percentage"""
        total = len(st.session_state.tasks)
        completed = sum(1 for t in st.session_state.tasks if t['status'] == 'success')
        return int((completed / total) * 100) if total > 0 else 0

    def render_progress_tracker(self):
        """Render visual progress tracker"""
        st.markdown("### 📊 Progress Tracker")

        # Phase progress
        phases = ["planning", "generation", "deployment", "validation", "finalization"]
        phase_colors = {
            "planning": "#3b82f6",
            "generation": "#8b5cf6",
            "deployment": "#f59e0b",
            "validation": "#10b981",
            "finalization": "#ec4899"
        }

        cols = st.columns(len(phases))
        for i, phase in enumerate(phases):
            with cols[i]:
                phase_tasks = [t for t in st.session_state.tasks if t['phase'] == phase]
                completed = sum(1 for t in phase_tasks if t['status'] == 'success')
                total = len(phase_tasks)

                # Status icon
                if all(t['status'] == 'success' for t in phase_tasks):
                    icon = "✅"
                elif any(t['status'] == 'running' for t in phase_tasks):
                    icon = "🔄"
                elif any(t['status'] == 'failed' for t in phase_tasks):
                    icon = "❌"
                else:
                    icon = "⏳"

                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="font-size: 24px;">{icon}</div>
                    <div style="font-weight: bold; color: {phase_colors[phase]};">
                        {phase.title()}
                    </div>
                    <div style="font-size: 12px; color: gray;">
                        {completed}/{total} tasks
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Overall progress bar
        progress = self.calculate_overall_progress()
        st.progress(progress / 100)

    def render_task_list(self):
        """Render detailed task list with live updates"""
        st.markdown("### 📋 Task Details")

        # Group tasks by phase
        phases = ["planning", "generation", "deployment", "validation", "finalization"]

        for phase in phases:
            phase_tasks = [t for t in st.session_state.tasks if t['phase'] == phase]
            if not phase_tasks:
                continue

            with st.expander(f"{phase.title()} Phase", expanded=(phase == st.session_state.current_phase)):
                for task in phase_tasks:
                    self.render_task_card(task)

    def render_task_card(self, task: Dict):
        """Render individual task card"""
        status_icons = {
            "pending": "⏳",
            "running": "🔄",
            "success": "✅",
            "failed": "❌",
            "warning": "⚠️"
        }

        col1, col2, col3 = st.columns([1, 4, 2])

        with col1:
            st.markdown(f"<div style='font-size: 24px; text-align: center;'>{status_icons[task['status']]}</div>",
                       unsafe_allow_html=True)

        with col2:
            st.markdown(f"**{task['name']}**")
            st.caption(task['description'])

            # Show progress for running tasks
            if task['status'] == 'running':
                st.progress(0.5)  # Indeterminate progress

            # Show validation results if available
            if task['id'] in st.session_state.validation_results:
                result = st.session_state.validation_results[task['id']]
                if result.get('message'):
                    if task['status'] == 'failed':
                        st.error(result['message'])
                    elif task['status'] == 'warning':
                        st.warning(result['message'])
                    else:
                        st.success(result['message'])

        with col3:
            # Task actions
            if task['status'] == 'failed':
                if st.button(f"Retry", key=f"retry_{task['id']}"):
                    self.retry_task(task['id'])
            elif task['status'] == 'pending' and self.can_start_task(task['id']):
                if st.button(f"Start", key=f"start_{task['id']}"):
                    self.start_task(task['id'])

    def can_start_task(self, task_id: str) -> bool:
        """Check if a task can be started based on dependencies"""
        task = next(t for t in st.session_state.tasks if t['id'] == task_id)

        # Define task dependencies
        dependencies = {
            "2": ["1"],  # Scenario depends on Research
            "3": ["2"],  # Data depends on Scenario
            "4": ["3"],  # Index creation depends on Data
            "5": ["4"],  # Upload depends on Index
            "6": ["2"],  # Queries depend on Scenario
            "7": ["5", "6"],  # Validation depends on Upload and Queries
            "8": ["7"],  # Agent config depends on Validation
            "9": ["8"],  # Documentation depends on Agent
            "10": ["9"]  # Final validation depends on Documentation
        }

        if task_id not in dependencies:
            return True

        for dep_id in dependencies[task_id]:
            dep_task = next(t for t in st.session_state.tasks if t['id'] == dep_id)
            if dep_task['status'] != 'success':
                return False

        return True

    def start_task(self, task_id: str):
        """Start a task execution"""
        for task in st.session_state.tasks:
            if task['id'] == task_id:
                task['status'] = 'running'
                task['started_at'] = datetime.now().isoformat()
                break

        # Save state to GitHub if available
        if self.github_manager:
            self.save_state_to_github()

        # Simulate task execution (in real app, this would call actual services)
        st.rerun()

    def retry_task(self, task_id: str):
        """Retry a failed task"""
        for task in st.session_state.tasks:
            if task['id'] == task_id:
                task['status'] = 'pending'
                task['error'] = None
                break
        st.rerun()

    def render_validation_panel(self):
        """Render validation results panel"""
        st.markdown("### ✅ Validation Results")

        if not st.session_state.validation_results:
            st.info("No validation results yet. Complete data upload and query generation first.")
            return

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        total_validations = len(st.session_state.validation_results)
        successful = sum(1 for r in st.session_state.validation_results.values()
                        if r.get('status') == 'success')
        warnings = sum(1 for r in st.session_state.validation_results.values()
                      if r.get('status') == 'warning')
        failures = sum(1 for r in st.session_state.validation_results.values()
                      if r.get('status') == 'failed')

        with col1:
            st.metric("Total Checks", total_validations)
        with col2:
            st.metric("Successful", successful, delta=f"{(successful/total_validations*100):.0f}%")
        with col3:
            st.metric("Warnings", warnings)
        with col4:
            st.metric("Failures", failures)

        # Detailed results
        with st.expander("Detailed Validation Results", expanded=False):
            for task_id, result in st.session_state.validation_results.items():
                task = next((t for t in st.session_state.tasks if t['id'] == task_id), None)
                if task:
                    st.markdown(f"**{task['name']}**")
                    if result.get('details'):
                        st.json(result['details'])

    def render_chat_interface(self):
        """Render conversational interface"""
        st.markdown("### 💬 Demo Assistant")

        # Display conversation history
        for msg in st.session_state.messages:
            with st.chat_message(msg['role']):
                st.markdown(msg['content'])

        # Input field
        if prompt := st.chat_input("Ask me anything about your demo..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Process and generate response
            response = self.process_chat_input(prompt)
            st.session_state.messages.append({"role": "assistant", "content": response})

            st.rerun()

    def process_chat_input(self, user_input: str) -> str:
        """Process user chat input and return response"""
        # This would integrate with LLM for actual processing
        # For now, return a helpful response based on current state

        progress = self.calculate_overall_progress()

        if "status" in user_input.lower():
            return f"Your demo is {progress}% complete. Currently working on {st.session_state.current_phase} phase."
        elif "help" in user_input.lower():
            return "I can help you create a custom demo! Start by providing your customer's name and website."
        else:
            return "I'm here to help you build your demo. What would you like to know?"

    def save_state_to_github(self):
        """Save current state to GitHub for persistence"""
        if not self.github_manager:
            return

        state = {
            "demo_id": st.session_state.demo_id,
            "tasks": st.session_state.tasks,
            "config": st.session_state.demo_config,
            "validation_results": st.session_state.validation_results,
            "updated_at": datetime.now().isoformat()
        }

        try:
            file_path = f"demos/{st.session_state.demo_id}/state.json"
            self.github_manager.save_file(file_path, json.dumps(state, indent=2))
            logger.info(f"State saved to GitHub: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save state to GitHub: {e}")

    def load_state_from_github(self, demo_id: str):
        """Load state from GitHub"""
        if not self.github_manager:
            return False

        try:
            file_path = f"demos/{demo_id}/state.json"
            content = self.github_manager.load_file(file_path)
            state = json.loads(content)

            st.session_state.demo_id = state['demo_id']
            st.session_state.tasks = state['tasks']
            st.session_state.demo_config = state['config']
            st.session_state.validation_results = state['validation_results']

            logger.info(f"State loaded from GitHub: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load state from GitHub: {e}")
            return False

    def render_sidebar(self):
        """Render sidebar with controls and info"""
        with st.sidebar:
            st.header("🎛️ Demo Controls")

            # Resume existing demo
            st.markdown("### Resume Demo")
            demo_id_input = st.text_input("Enter Demo ID to resume:")
            if st.button("Load Demo"):
                if self.load_state_from_github(demo_id_input):
                    st.success("Demo loaded successfully!")
                    st.rerun()
                else:
                    st.error("Failed to load demo")

            st.divider()

            # Export options
            st.markdown("### Export Options")

            if st.button("📄 Export Demo Guide"):
                self.export_demo_guide()

            if st.button("📊 Export Validation Report"):
                self.export_validation_report()

            if st.button("💾 Save State to GitHub"):
                self.save_state_to_github()
                st.success("State saved!")

            st.divider()

            # Configuration
            st.markdown("### Configuration")

            github_token = st.text_input(
                "GitHub Token (optional):",
                type="password",
                help="For saving/loading demo state"
            )
            if github_token:
                st.session_state.github_token = github_token

            es_host = st.text_input(
                "Elasticsearch Host:",
                value=st.session_state.get('es_host', 'localhost:9200')
            )
            st.session_state.es_host = es_host

    def export_demo_guide(self):
        """Export demo guide as markdown"""
        # Generate demo guide markdown
        guide = f"# Demo Guide: {st.session_state.demo_config.get('customer', 'Unknown')}\n\n"
        guide += f"Demo ID: {st.session_state.demo_id}\n\n"
        # Add more content...

        st.download_button(
            label="Download Demo Guide",
            data=guide,
            file_name=f"demo_guide_{st.session_state.demo_id}.md",
            mime="text/markdown"
        )

    def export_validation_report(self):
        """Export validation report"""
        report = {"validation_results": st.session_state.validation_results}

        st.download_button(
            label="Download Validation Report",
            data=json.dumps(report, indent=2),
            file_name=f"validation_report_{st.session_state.demo_id}.json",
            mime="application/json"
        )

    def run(self):
        """Main application entry point"""
        self.render_sidebar()
        self.render_header()

        # Main content area with tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Progress", "💬 Assistant", "✅ Validation", "📦 Artifacts"])

        with tab1:
            self.render_progress_tracker()
            st.divider()
            self.render_task_list()

        with tab2:
            self.render_chat_interface()

        with tab3:
            self.render_validation_panel()

        with tab4:
            self.render_artifacts()

    def render_artifacts(self):
        """Render generated artifacts"""
        st.markdown("### 📦 Generated Artifacts")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Data Files")
            if st.session_state.demo_config.get('datasets'):
                for dataset in st.session_state.demo_config['datasets']:
                    st.markdown(f"- 📄 {dataset}")
            else:
                st.info("No datasets generated yet")

        with col2:
            st.markdown("#### ES|QL Queries")
            if st.session_state.demo_config.get('queries'):
                for query in st.session_state.demo_config['queries']:
                    st.markdown(f"- 🔍 {query}")
            else:
                st.info("No queries generated yet")

if __name__ == "__main__":
    app = DemoBuilderApp()
    app.run()