import os
import re
import json
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgent:
    """
    SKELETON: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Students should implement the core loop logic and tool execution.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []
        self.tool_results: Dict[str, Any] = {}

    def get_system_prompt(self) -> str:
        """
        TODO: Implement the system prompt that instructs the agent to follow ReAct.
        Should include:
        1.  Available tools and their descriptions.
        2.  Format instructions: Thought, Action, Observation.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return (
            "You are an intelligent assistant. You have access to the following tools:\n"
            f"{tool_descriptions}\n\n"
            "Use the following format:\n"
            "Thought: your line of reasoning.\n"
            "Action: tool_name(arguments)\n"
            "Observation: result of the tool call.\n"
            "... (repeat Thought/Action/Observation if needed)\n"
            "Final Answer: your final response.\n\n"
            "IMPORTANT RULES:\n"
            "- To call a tool with no arguments: Action: tool_name()\n"
            "- To pass a previous tool's result as input, use its name as the argument.\n"
            "  Example: after calling weather_forecast(), you can do:\n"
            "  Action: suggest_outfit(weather_forecast)\n"
            "  This automatically passes the weather_forecast result to suggest_outfit.\n"
            "- For cafe recommendation requests, follow this exact order:\n"
            "  1) Action: weather_forecast()\n"
            "  2) Action: suggest_outfit(weather_forecast)\n"
            "  3) Action: get_nearby_places_serpapi()\n"
            "  Then provide Final Answer combining outfit + nearby cafes.\n"
            "  In the cafe list, ALWAYS include distance for each place and keep them sorted by nearest first.\n"
            "- Final Answer MUST be in Vietnamese and strictly follow this template:\n"
            "  Thời tiết hiện tại ... nên bạn có thể mặc ...\n"
            "  Các quán cafe ở gần:\n"
            "  1. <Tên quán 1> - <Khoảng cách>\n"
            "  2. <Tên quán 2> - <Khoảng cách>\n"
            "  3. <Tên quán 3> - <Khoảng cách>\n"
            "- Do not include markdown bullets, JSON, code fences, or extra headings in Final Answer.\n"
            "- You MUST only output ONE Thought + ONE Action per turn, then wait for the Observation.\n"
            "- When you have enough information, respond with Final Answer."
        )

    def run(self, user_input: str) -> str:
        """
        TODO: Implement the ReAct loop logic.
        1. Generate Thought + Action.
        2. Parse Action and execute Tool.
        3. Append Observation to prompt and repeat until Final Answer.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        current_prompt = f"User question: {user_input}"
        steps = 0
        self.tool_results = {}

        while steps < self.max_steps:
            result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            content = (result.get("content") or "").strip()
            self.history.append({"step": steps + 1, "llm_output": content})

            # If the model already gives a final answer, stop immediately.
            final_match = re.search(r"Final Answer:\s*(.*)", content, flags=re.IGNORECASE | re.DOTALL)
            if final_match:
                final_answer = final_match.group(1).strip()
                logger.log_event("AGENT_END", {"steps": steps + 1, "reason": "final_answer"})
                return self._append_cafe_distances(final_answer or content)

            # Parse Action in the format: Action: tool_name(arguments)
            action_match = re.search(
                r"Action:\s*([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)\s*$",
                content,
                flags=re.IGNORECASE | re.DOTALL,
            )
            if not action_match:
                # Fallback: if no valid Action/Final Answer, return raw model output.
                logger.log_event("AGENT_END", {"steps": steps + 1, "reason": "no_action"})
                return content or "Model did not return an actionable response."

            tool_name = action_match.group(1).strip()
            args = action_match.group(2).strip()
            tool_result = self._execute_tool(tool_name, args)
            self.history.append(
                {"step": steps + 1, "action": tool_name, "args": args, "observation": tool_result}
            )

            observation_text = tool_result
            if len(observation_text) > 2000:
                observation_text = (
                    observation_text[:2000]
                    + f"\n... (truncated, full result stored as '{tool_name}')"
                )

            current_prompt = (
                f"{current_prompt}\n\n"
                f"Assistant output:\n{content}\n"
                f"Observation: {observation_text}\n"
                f"Continue the Thought-Action-Observation loop, or provide Final Answer."
            )
            steps += 1
            
        logger.log_event("AGENT_END", {"steps": steps, "reason": "max_steps"})
        return "Reached max steps without Final Answer."

    def _append_cafe_distances(self, answer: str) -> str:
        """
        Ensure final output includes nearby cafe distances when available.
        """
        nearby_raw = self.tool_results.get("get_nearby_places_serpapi")
        if not nearby_raw:
            return answer

        try:
            places = nearby_raw if isinstance(nearby_raw, list) else json.loads(str(nearby_raw))
        except Exception:
            return answer

        if not isinstance(places, list) or not places:
            return answer

        lines = []
        for idx, place in enumerate(places, start=1):
            name = place.get("name") or "Không rõ tên"
            distance = place.get("distance") or "Không rõ khoảng cách"
            address = place.get("address") or "Không rõ địa chỉ"
            rating = place.get("rating")
            if rating is None:
                lines.append(f"{idx}. {name} - {distance} - {address}")
            else:
                lines.append(f"{idx}. {name} - {distance} - {address} (Rating: {rating})")

        cafe_block = "Quán cafe gần bạn (gần đến xa):\n" + "\n".join(lines)
        if "Quán cafe gần bạn (gần đến xa):" in answer:
            return answer
        return f"{answer}\n\n{cafe_block}"

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Execute a tool by name.
        Supports referencing a previous tool's stored result as the argument,
        e.g. args="weather_forecast" will inject the saved result of that tool.
        """
        for tool in self.tools:
            if tool['name'] == tool_name:
                func = tool.get("func")
                if not callable(func):
                    return f"Tool {tool_name} is not callable."

                try:
                    parsed_args = (args or "").strip()

                    # If the argument is a previous tool name, inject its stored result
                    if parsed_args in self.tool_results:
                        result = func(self.tool_results[parsed_args])
                    elif not parsed_args:
                        result = func()
                    else:
                        try:
                            payload = json.loads(parsed_args)
                        except json.JSONDecodeError:
                            payload = parsed_args
                        result = func(payload)

                    self.tool_results[tool_name] = result
                except Exception as e:
                    return f"Tool {tool_name} error: {e}"

                return str(result)
        return f"Tool {tool_name} not found."
