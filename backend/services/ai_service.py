import json
import re
from backend.ai.llm_client import get_llm

def call_llm_and_parse_json(prompt, llm_config=None, temperature=0):
    """
    Helper to call LLM with a prompt and extract/parse JSON from its response.
    """
    llm = get_llm(llm_config or {"model": "gemini-2.5-flash-lite", "mode": "default"}, temperature=temperature)
    response = llm.invoke(prompt)
    
    try:
        # Extract JSON using regex for robustness
        content = response.content
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group())
        
        # Fallback to direct replace if regex fails
        content = content.replace('```json', '').replace('```', '').strip()
        return json.loads(content)
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        return {}
