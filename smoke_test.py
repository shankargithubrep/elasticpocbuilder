#!/usr/bin/env python3
"""Quick smoke test for 3-call refactor"""

from src.framework.orchestrator import ModularDemoOrchestrator
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    orchestrator = ModularDemoOrchestrator(client)

    config = {
        'company_name': 'SmokeTest Corp',
        'department': 'Marketing',
        'industry': 'SaaS',
        'pain_points': ['slow campaigns'],
        'use_cases': ['campaign analytics'],
        'scale': '500 users',
        'metrics': ['conversion']
    }

    print('🧪 Running end-to-end smoke test...')
    print()
    result = orchestrator.generate_new_demo(config)
    print()
    print(f'✅ Demo generated: {result["module_path"]}')
    print(f'✅ Queries generated: {len(result["queries"])} total')

    # Verify query types
    scripted = [q for q in result['queries'] if q.get('query_type') == 'scripted']
    param = [q for q in result['queries'] if q.get('query_type') == 'parameterized']
    rag = [q for q in result['queries'] if q.get('query_type') == 'rag']

    print()
    print('📊 Query Breakdown:')
    print(f'  - Scripted: {len(scripted)}')
    print(f'  - Parameterized: {len(param)}')
    print(f'  - RAG: {len(rag)}')
    print()

    if scripted and param and rag:
        print('🎉 SMOKE TEST PASSED!')
        print('✅ Ready for user testing')
        return 0
    else:
        print('❌ SMOKE TEST FAILED - Missing query types')
        return 1

if __name__ == '__main__':
    exit(main())
